"""Tests for the transformers vs. GGUF dispatch in api.services.pipeline.call_model.

GGUF support was added so the API can be served from a <10GB container (the
transformers + torch runtime alone is 5-7GB, before even counting the model —
see the Docker sizing discussion). The transformers path stays the default for
HF-style paths/repo-ids (used by the current Jupiter deployment); GGUF kicks
in only when model_path ends in ".gguf", so nothing about the working
deployment changes.

llama_cpp is not installed in this dev environment (it's an optional,
serving-time-only dependency) — tests that exercise _call_model_gguf directly
inject a fake module into sys.modules so the lazy `from llama_cpp import
Llama` import inside the function resolves to a mock instead of failing.
"""

import sys
import types
from unittest.mock import MagicMock

import pytest

import api.services.pipeline as pipeline


def _fake_llama_module(chat_completion_return):
    fake_llama_cls = MagicMock()
    fake_llama_instance = MagicMock()
    fake_llama_instance.create_chat_completion.return_value = chat_completion_return
    fake_llama_cls.return_value = fake_llama_instance
    module = types.ModuleType("llama_cpp")
    module.Llama = fake_llama_cls
    return module, fake_llama_cls, fake_llama_instance


@pytest.fixture(autouse=True)
def clear_gguf_cache():
    pipeline._gguf_model_cache.clear()
    yield
    pipeline._gguf_model_cache.clear()


def test_call_model_dispatches_to_gguf_for_gguf_path(monkeypatch):
    called = []
    monkeypatch.setattr(pipeline, "_call_model_gguf", lambda *a, **kw: called.append("gguf") or {"inference_mode": "fine-tuned"})
    monkeypatch.setattr(pipeline, "_call_model_transformers", lambda *a, **kw: called.append("transformers"))

    pipeline.call_model("prompt", "/models/archx-gemma4-Q4_K_M.gguf", mock=False, language="fr")

    assert called == ["gguf"]


def test_call_model_dispatches_to_transformers_for_hf_path(monkeypatch):
    called = []
    monkeypatch.setattr(pipeline, "_call_model_gguf", lambda *a, **kw: called.append("gguf"))
    monkeypatch.setattr(pipeline, "_call_model_transformers", lambda *a, **kw: called.append("transformers") or {"inference_mode": "fine-tuned"})

    pipeline.call_model("prompt", "Karmelkke/archx-gemma4-12b-merged", mock=False, language="fr")

    assert called == ["transformers"]


def test_extract_json_response_tags_inference_mode():
    result = pipeline._extract_json_response('{"recommendation": "refactoring"}')
    assert result == {"recommendation": "refactoring", "inference_mode": "fine-tuned"}


def test_extract_json_response_returns_none_without_json():
    assert pipeline._extract_json_response("no json here, model rambled instead") is None


def test_call_model_gguf_builds_plain_string_messages_and_parses_response(monkeypatch):
    fake_module, fake_cls, fake_instance = _fake_llama_module(
        {"choices": [{"message": {"content": '{"recommendation": "refactoring"}'}}]}
    )
    monkeypatch.setitem(sys.modules, "llama_cpp", fake_module)

    result = pipeline._call_model_gguf("prompt text", "/models/archx.gguf", "fr")

    assert result == {"recommendation": "refactoring", "inference_mode": "fine-tuned"}

    _, load_kwargs = fake_cls.call_args
    assert load_kwargs["model_path"] == "/models/archx.gguf"

    _, call_kwargs = fake_instance.create_chat_completion.call_args
    messages = call_kwargs["messages"]
    # Plain string content (not the [{'type':'text',...}] list used by the
    # transformers path) — see _call_model_gguf's docstring note on why.
    assert messages[0] == {"role": "system", "content": pipeline.SYSTEM_PROMPT["fr"]}
    assert messages[1] == {"role": "user", "content": "prompt text"}


def test_call_model_gguf_returns_none_when_no_json_in_response(monkeypatch):
    fake_module, _, _ = _fake_llama_module(
        {"choices": [{"message": {"content": "I cannot analyze this, sorry."}}]}
    )
    monkeypatch.setitem(sys.modules, "llama_cpp", fake_module)

    assert pipeline._call_model_gguf("prompt", "/models/archx.gguf", "fr") is None


def test_call_model_gguf_caches_loaded_model_across_calls(monkeypatch):
    fake_module, fake_cls, fake_instance = _fake_llama_module(
        {"choices": [{"message": {"content": '{"recommendation": "refactoring"}'}}]}
    )
    monkeypatch.setitem(sys.modules, "llama_cpp", fake_module)

    pipeline._call_model_gguf("prompt 1", "/models/archx.gguf", "fr")
    pipeline._call_model_gguf("prompt 2", "/models/archx.gguf", "fr")

    fake_cls.assert_called_once()  # model loaded once, reused on the second call
    assert fake_instance.create_chat_completion.call_count == 2


def test_call_model_falls_back_to_mock_when_gguf_path_raises(monkeypatch):
    def _boom(*a, **kw):
        raise RuntimeError("model file not found")

    monkeypatch.setattr(pipeline, "_call_model_gguf", _boom)

    result = pipeline.call_model("prompt", "/models/archx.gguf", mock=False, language="fr")

    assert result["inference_mode"] == "mock"


def test_call_model_falls_back_to_mock_when_result_is_none(monkeypatch):
    # e.g. the model responded but with no parseable JSON — same fallback as before the split.
    monkeypatch.setattr(pipeline, "_call_model_gguf", lambda *a, **kw: None)

    result = pipeline.call_model("prompt", "/models/archx.gguf", mock=False, language="fr")

    assert result["inference_mode"] == "mock"
