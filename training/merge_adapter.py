"""
merge_adapter.py
------------------
Fusionne l'adaptateur LoRA entraîné avec le modèle de base Gemma pour
produire un modèle unique — plus simple à servir (ex: avec vLLM sur AMD
Developer Cloud) qu'un couple base+adaptateur séparé.

Usage :
    python -m training.merge_adapter \
        --base google/gemma-4-12B-it \
        --adapter ./architect-insight-lora \
        --output ./architect-insight-merged
"""

from __future__ import annotations

import argparse

import torch


def main() -> None:
    parser = argparse.ArgumentParser(description="Fusionne un adaptateur LoRA avec son modèle de base")
    parser.add_argument("--base", required=True, help="Nom/chemin du modèle de base (ex: google/gemma-4-12B-it)")
    parser.add_argument("--adapter", required=True, help="Chemin de l'adaptateur LoRA entraîné (dossier output de train_lora.py)")
    parser.add_argument("--output", required=True, help="Dossier de sortie pour le modèle fusionné")
    args = parser.parse_args()

    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    print(f"Chargement du modèle de base : {args.base}")
    base_model = AutoModelForCausalLM.from_pretrained(
        args.base, torch_dtype=torch.bfloat16, device_map="auto"
    )
    tokenizer = AutoTokenizer.from_pretrained(args.base)

    print(f"Chargement de l'adaptateur : {args.adapter}")
    model = PeftModel.from_pretrained(base_model, args.adapter)

    print("Fusion en cours (merge_and_unload)...")
    merged = model.merge_and_unload()

    print(f"Sauvegarde du modèle fusionné dans {args.output}")
    merged.save_pretrained(args.output, safe_serialization=True)
    tokenizer.save_pretrained(args.output)

    print("Terminé. Ce dossier peut être servi directement (ex: vllm serve <output>).")


if __name__ == "__main__":
    main()
