"""Regression tests for the debt-map data exposure fix.

complexity_hotspots used to omit num_lines/num_imports even though
FileMetrics already computed them (architect_insight/metrics/complexity.py) —
they just weren't included in collector.py's dict comprehension. Also locks
in that collect()'s output is JSON-serializable end-to-end now that Java
analysis can contribute real (dataclass-based) findings.
"""

import json

from architect_insight.collector import collect


def test_complexity_hotspots_expose_num_lines_and_num_imports(tmp_path):
    (tmp_path / "big.py").write_text(
        "import os\nimport sys\nimport json\n\n"
        + "\n".join(f"def f{i}():\n    pass\n" for i in range(5))
    )

    report = collect(str(tmp_path))

    assert report["complexity_hotspots"], "expected at least one hotspot"
    hotspot = report["complexity_hotspots"][0]
    assert "num_lines" in hotspot
    assert "num_imports" in hotspot
    assert hotspot["num_imports"] == 3
    assert hotspot["num_lines"] > 0


def test_collect_output_is_json_serializable_with_java_present(tmp_path):
    (tmp_path / "Foo.java").write_text("public class Foo { public void bar() {} }\n")
    (tmp_path / "main.py").write_text("def main():\n    pass\n")

    report = collect(str(tmp_path))

    # Must not raise — java_analysis["files"] (raw JavaFileMetrics dataclasses)
    # must be popped before reaching the final report.
    json.dumps(report, ensure_ascii=False)
    assert "files" not in report["java_analysis"]
