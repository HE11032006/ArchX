"""
train_lora.py
---------------
Fine-tuning LoRA de Gemma 4 (12B) sur AMD Instinct MI300X via ROCm.

Choix techniques (et pourquoi) :
  - bf16 pur, PAS de bitsandbytes/4-bit : sur ROCm, bitsandbytes n'a qu'un
    support expérimental (source de bugs d'installation). Le MI300X a 192 Go
    de VRAM, largement assez pour un 12B en bf16 + adaptateurs LoRA — la
    quantization n'apporte donc rien ici, seulement du risque.
  - bf16 plutôt que fp16 : Gemma est entraîné/optimisé pour bfloat16, dont la
    plage d'exposant plus large évite les instabilités numériques que fp16
    peut causer sur ce type de modèle.
  - formatting_func + tokenizer.apply_chat_template : évite de coder en dur
    le format de tags de Gemma (qui a changé entre les générations) — on
    laisse le tokenizer officiel s'en charger.
  - LoRA (pas de full fine-tuning) : suffisant pour apprendre un style de
    raisonnement sur ~800 exemples, rapide (quelques heures max sur MI300X).

Suit le pattern validé par le tutoriel officiel AMD ROCm AI Developer Hub
("Fine-tuning with the Hugging Face ecosystem (TRL)"), adapté ici à un usage
texte pur (pas de VLM) et à Gemma 4.

Prérequis (voir SETUP_AMD_CLOUD.md pour le détail) :
    pip install "transformers>=4.47" "trl>=0.12" "peft>=0.13" "accelerate>=1.1" datasets

Usage :
    python -m training.train_lora \
        --data dataset_generation/training_data.jsonl \
        --model google/gemma-4-12B-it \
        --output ./architect-insight-lora
"""

from __future__ import annotations

import argparse
import gc
import json
import time


def clear_gpu_memory():
    """Libère la VRAM entre les étapes (utile en notebook, inoffensif en script)."""
    import torch

    gc.collect()
    time.sleep(1)
    if torch.cuda.is_available():  # sur ROCm, torch.cuda.* reste l'API utilisée (HIP s'y branche)
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
    gc.collect()


def load_jsonl_as_messages(path: str) -> list[list[dict]]:
    """Charge le JSONL produit par generate_dataset.py et le convertit en
    listes de messages [system, user, assistant] via format_for_training."""
    from .format_for_training import record_to_messages

    conversations = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            conversations.append(record_to_messages(record))
    return conversations


def build_formatting_func(tokenizer):
    """Retourne la fonction que SFTTrainer appellera pour transformer chaque
    exemple (déjà sous forme de liste de messages) en texte final via le
    chat template natif du tokenizer — indispensable pour que Gemma
    reconnaisse la structure system/user/assistant."""

    def formatting_func(example):
        # `example["messages"]` car on stocke les conversations dans une
        # colonne "messages" du Dataset HF (voir main()).
        return tokenizer.apply_chat_template(
            example["messages"], tokenize=False, add_generation_prompt=False
        )

    return formatting_func


def main() -> None:
    parser = argparse.ArgumentParser(description="Fine-tuning LoRA de Gemma 4 sur AMD MI300X (ROCm)")
    parser.add_argument("--data", required=True, help="Fichier JSONL produit par generate_dataset.py")
    parser.add_argument("--model", default="google/gemma-4-12B-it")
    parser.add_argument("--output", default="./architect-insight-lora")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--lora-r", type=int, default=16)
    parser.add_argument("--lora-alpha", type=int, default=32)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--grad-accum", type=int, default=8)
    parser.add_argument("--eval-fraction", type=float, default=0.05, help="Part du dataset gardée pour la validation")
    parser.add_argument("--report-to", default="none", help="'wandb' si tu veux le logging W&B, sinon 'none'")
    args = parser.parse_args()

    # --- imports lourds faits ici seulement (pas au chargement du module) ---
    import torch
    from datasets import Dataset
    from peft import LoraConfig, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from trl import SFTConfig, SFTTrainer

    print(f"[1/6] Chargement du tokenizer et du dataset depuis {args.data}")
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    conversations = load_jsonl_as_messages(args.data)
    print(f"       {len(conversations)} exemples chargés")

    dataset = Dataset.from_dict({"messages": conversations})
    split = dataset.train_test_split(test_size=args.eval_fraction, seed=42)
    train_dataset, eval_dataset = split["train"], split["test"]
    print(f"       train={len(train_dataset)}  eval={len(eval_dataset)}")

    print(f"[2/6] Chargement de {args.model} en bf16 (device_map=auto)")
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        torch_dtype=torch.bfloat16,
        device_map="auto",
    )

    print("[3/6] Application de la configuration LoRA")
    lora_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=0.05,
        bias="none",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()  # doit afficher < 2% de paramètres entraînables

    print("[4/6] Configuration de l'entraînement (SFTConfig)")
    training_args = SFTConfig(
        output_dir=args.output,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        optim="adamw_torch_fused",
        learning_rate=args.lr,
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        max_grad_norm=0.3,
        logging_steps=5,
        eval_strategy="steps",
        eval_steps=25,
        save_strategy="steps",
        save_steps=50,
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        bf16=True,          # cohérent avec le chargement du modèle en bf16
        fp16=False,         # Gemma est instable en fp16 pur, on n'utilise pas ce mode
        tf32=False,
        report_to=args.report_to,
        dataset_text_field="",              # on fournit formatting_func, pas un champ texte direct
        dataset_kwargs={"skip_prepare_dataset": True},
    )
    training_args.remove_unused_columns = False

    print("[5/6] Lancement de l'entraînement")
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        formatting_func=build_formatting_func(tokenizer),
        processing_class=tokenizer,
    )
    trainer.train()

    print(f"[6/6] Sauvegarde de l'adaptateur LoRA dans {args.output}")
    trainer.save_model(args.output)
    tokenizer.save_pretrained(args.output)

    clear_gpu_memory()
    print("Terminé. Utilise merge_adapter.py pour fusionner l'adaptateur avec le modèle de base si besoin.")


if __name__ == "__main__":
    main()
