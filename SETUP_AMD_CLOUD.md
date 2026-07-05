# Architect-Insight — Comment tout faire tourner (dans l'ordre)

Précision d'abord : ce projet est en Python, il n'y a rien à "compiler" —
chaque script s'exécute directement. Ce qui suit est l'**ordre d'exécution**,
pas une compilation.

## Vue d'ensemble

```
1. Provisionner l'instance AMD Developer Cloud (MI300X)
2. Générer le dataset (LOCAL, pas besoin de GPU — juste l'API Anthropic)
3. Relire les exemples flagués
4. [instance AMD] Fine-tuner Gemma 4 en LoRA
5. [instance AMD] Fusionner l'adaptateur (optionnel, pour servir plus simplement)
6. Brancher collector.py → modèle fine-tuné → démo
```

Étapes 2-3 ne nécessitent aucun GPU : fais-les sur ta machine, ça ne coûte
pas d'heures de crédit AMD. Ne réserve ton instance MI300X qu'à partir de
l'étape 4.

---

## Étape 1 — Provisionner l'instance AMD Developer Cloud

1. Va sur https://devcloud.amd.com, connecte-toi (GitHub ou email).
2. Crée une VM et choisis l'image **"PyTorch" (Quick Start)**, pas "Vanilla
   ROCm" — l'image PyTorch vient avec ROCm + PyTorch déjà installés dans un
   conteneur Docker, plus JupyterLab prêt à l'emploi. Ça t'évite exactement
   le genre de galère d'installation qu'on avait identifiée avec le script
   ROCm générique (wheel PyTorch obsolète, bitsandbytes fragile sur ROCm).
3. Choisis une instance MI300X (192 Go de VRAM — largement assez pour un
   12B en bf16 + LoRA).
4. Accède à l'environnement via JupyterLab (lien fourni à la création de la
   VM) ou SSH si tu préfères le terminal.

Si tu préfères partir d'une image "Vanilla ROCm" (contrôle total, plus de
travail) plutôt que du Quick Start PyTorch, le tutoriel officiel AMD donne
la séquence Docker exacte :

```bash
docker pull rocm/pytorch:rocm6.2.3_ubuntu22.04_py3.10_pytorch_release_2.3.0
# (vérifie sur Docker Hub s'il existe un tag plus récent basé sur ROCm 7.x)

docker run -it --rm \
  --network=host \
  --device=/dev/kfd --device=/dev/dri \
  --group-add=video --ipc=host \
  --cap-add=SYS_PTRACE --security-opt seccomp=unconfined \
  --shm-size 8G \
  -v $(pwd):/workspace -w /workspace \
  rocm/pytorch:rocm6.2.3_ubuntu22.04_py3.10_pytorch_release_2.3.0
```

Dans les deux cas, vérifie que le GPU est bien vu avant d'aller plus loin :

```bash
amd-smi   # liste les GPU AMD détectés
python3 -c "import torch; print(torch.cuda.is_available(), torch.cuda.device_count())"
```

---

## Étape 2 — Générer le dataset (en local, sans GPU)

```bash
pip install anthropic --break-system-packages   # ou dans un venv

export ANTHROPIC_API_KEY=sk-...

cd architect-insight-tools

# Vérifier d'abord que tout tourne sans consommer d'appels API
python3 -m dataset_generation.test_validation
python3 -m dataset_generation.generate_dataset --n 20 --dry-run

# Génération réelle : 400 scénarios x 2 langues = jusqu'à 800 exemples
python3 -m dataset_generation.generate_dataset \
    --n 400 --languages fr en \
    --out dataset_generation/training_data.jsonl \
    --review-out dataset_generation/to_review.jsonl
```

## Étape 3 — Relire les exemples flagués

```bash
wc -l dataset_generation/to_review.jsonl   # combien à relire ?
cat dataset_generation/to_review.jsonl | python3 -m json.tool
```

Corrige à la main ou supprime les entrées incohérentes. Ne saute pas cette
étape — c'est elle qui évite d'entraîner sur du bruit (voir le README de
`dataset_generation/` pour le détail des garde-fous).

Une fois propre, transfère `training_data.jsonl` sur l'instance AMD (via
`scp`, l'upload JupyterLab, ou un dépôt Git privé).

---

## Étape 4 — Fine-tuning LoRA (sur l'instance AMD MI300X)

```bash
pip install "transformers>=4.47" "trl>=0.12" "peft>=0.13" "accelerate>=1.1" datasets huggingface_hub

huggingface-cli login   # nécessaire pour télécharger Gemma 4 (modèle "gated")

python3 -m training.train_lora \
    --data dataset_generation/training_data.jsonl \
    --model google/gemma-4-12B-it \
    --output ./architect-insight-lora \
    --epochs 3
```

Compte large : avec ~800 exemples et un 12B en LoRA sur MI300X, ça devrait
tourner en quelques heures, pas en jours. Surveille `eval_loss` dans les
logs — s'il remonte alors que la loss d'entraînement continue de baisser,
c'est de l'overfitting (réduis `--epochs` ou augmente le dataset).

## Étape 5 — Fusionner l'adaptateur (optionnel)

Utile si tu veux servir le modèle avec vLLM sans gérer base+adaptateur séparément :

```bash
python3 -m training.merge_adapter \
    --base google/gemma-4-12B-it \
    --adapter ./architect-insight-lora \
    --output ./architect-insight-merged
```

## Étape 6 — Brancher sur la démo

Le pipeline de démo (pas encore construit) fera :
`architect_insight/collector.py` (vraies métriques d'un repo) →
`training/format_for_training.py::build_user_message()` (même fonction
que celle utilisée à l'entraînement — voir le commentaire dans ce fichier
sur l'importance de cette cohérence) → modèle fine-tuné → JSON de sortie →
`cost_calculator.py` (pas encore écrit) pour ajouter les chiffres calculés.

## Point de vigilance sur le format des métriques

`collector.py` produit des `git_hotspots` sous forme de liste (un ratio par
fichier chaud), alors que les scénarios synthétiques d'entraînement n'ont
qu'un seul `top_hotspot_bugfix_ratio` agrégé. Ce n'est pas bloquant pour
lancer un premier entraînement, mais il faudra harmoniser les deux formats
avant de brancher le vrai collecteur sur le modèle fine-tuné, sinon le
modèle verra un format légèrement différent de celui vu à l'entraînement.
