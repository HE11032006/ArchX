# Guide de Fine-Tuning AMD Cloud — Pour le Collaborateur

Ce guide s'adresse à toi Karmel qui va exécuter l'entraînement du modèle Gemma  
sur le **AMD Developer Cloud** en utilisant ses crédits GPU MI300X/MI200X. Bon assure toi que c'est bien ça les GPU sinon dis moi ça s'il y a un pb.

---

## Ce que tu vas faire

Fine-tuner le modèle **Gemma** avec **LoRA** sur notre dataset d'analyses architecturales.  
Tout est automatisé — tu n'as qu'à exécuter les cellules du notebook dans l'ordre.

**Durée totale estimée : 1h à 1h45**

---

## Étape 1 — Prérequis (à faire une seule fois)

### 1.1 Créer un compte Hugging Face
Va sur **https://huggingface.co** et crée un compte gratuit si tu n'en as pas.

### 1.2 Accepter les conditions d'utilisation de Gemma
Va sur cette page et clique sur **"Agree and access repository"** :
- **https://huggingface.co/google/gemma-2-9b-it**

> Sans ça, le téléchargement du modèle échouera avec une erreur 401.

### 1.3 Créer un token Hugging Face
Va sur **https://huggingface.co/settings/tokens**  
→ Clique sur "New token" → Type "Read" → Copie le token (commence par `hf_...`)  
→ **Garde-le précieusement**, le notebook te le demandera.

### 1.4 Se connecter sur AMD Developer Cloud
Va sur **https://devcloud.amd.com** et connecte-toi.

---

## Étape 2 — Créer l'instance GPU sur AMD

1. Clique sur **"Launch Instance"** (ou "Create VM")
2. Choisis l'image : **"PyTorch Quick Start"** ← IMPORTANT, pas "Vanilla ROCm"
3. Choisis le GPU : **MI300X** (ou MI200X si indisponible)
4. Lance l'instance et attends que le statut passe au vert (2–5 min)
5. Clique sur **"Open JupyterLab"**

---

## Étape 3 — Uploader les fichiers dans JupyterLab

Tu vas trouver ces fichiers dans le repo GitHub (branche `develop`) :

| Fichier | Où le mettre dans JupyterLab |
|---|---|
| `training/finetune_lora_amd.ipynb` | Racine du JupyterLab |
| `dataset_generation/training_data.jsonl` | Racine du JupyterLab |

**Comment uploader :**
1. Dans le panneau gauche de JupyterLab, clique sur l'icône ⬆️ (Upload Files)
2. Sélectionne les deux fichiers depuis ton PC
3. Attends que l'upload soit terminé

**Alternative (plus rapide si tu as git) :**
Ouvre un terminal dans JupyterLab (File → New → Terminal) et tape :
```bash
git clone -b develop https://github.com/<username>/<repo>.git
cd architect-insight-tools
# Le notebook et le dataset sont déjà là !
```

---

## Étape 4 — Ouvrir et exécuter le notebook

1. Double-clique sur `finetune_lora_amd.ipynb`
2. Exécute chaque cellule dans l'ordre : clic sur la cellule → **Shift + Enter**
3. Attends que `[*]` disparaisse avant de passer à la suivante
### Ce que tu dois voir à chaque étape

| Cellule | Signe que tout va bien |
|---|---|
| 1 — Installation | `Toutes les dépendances sont installées.` |
| 2 — GPU | Nom du GPU AMD + VRAM + `MODE SÉLECTIONNÉ : bf16` |
| 3 — Hugging Face | Le notebook te demande ton token → colle ton `hf_...` → `Connexion réussie` |
| 4 — Dataset | `→ X exemples chargés.` + un extrait de texte |
| 5 — Modèle | Barre de téléchargement (~18 Go) puis ` Modèle chargé en bf16.` |
| 6 — LoRA | `trainable params: ... || trainable%: ~1-2%` |
| 7 — Entraînement | Logs de loss qui **descendent** (ex: 1.8 → 1.2 → 0.8 → 0.5) |
| 8 — Sauvegarde | ` Adaptateur LoRA sauvegardé avec succès !` |
| 9 — Test | Une réponse JSON générée par le modèle fine-tuné |

---

## Comment savoir que l'entraînement se passe bien ?

Pendant la cellule 7, tu verras des logs comme ceci :
```
{'loss': 1.85, 'step': 10}   ← Normal au début
{'loss': 1.23, 'step': 25}   ← Ça descend = bon signe ✅
{'loss': 0.81, 'step': 50}   ← Très bon ✅
{'loss': 0.52, 'eval_loss': 0.61, 'step': 75}   ← Excellent ✅
```

 **Problèmes et solutions :**

| Erreur | Cause | Solution |
|---|---|---|
| `401 Unauthorized` | Token HF invalide ou modèle non accepté | Re-login HF + accepter Gemma sur HF |
| `CUDA out of memory` | VRAM insuffisante | Réduire `per_device_train_batch_size` à 1 |
| `loss NaN` ou `loss > 5` | Learning rate trop élevé | Changer `learning_rate` à `1e-4` |
| `eval_loss` remonte | Overfitting | Réduire `num_train_epochs` à 2 |

---

## Étape 5 — Récupérer le modèle fine-tuné

>  IMPORTANT : Fais ça **avant de fermer l'instance** pour ne pas perdre le travail !

### Option A : Télécharger depuis JupyterLab
1. Dans le panneau gauche, clic droit sur le dossier `architect-insight-lora-final/`
2. Clique sur **"Download"**
3. Archive zippée téléchargée sur ton PC ✅

### Option B : Pusher sur Hugging Face Hub
Dans un terminal JupyterLab :
```bash
huggingface-cli upload <ton-username>/archx-lora ./architect-insight-lora-final
```

### Option C : Pusher dans le repo GitHub
```bash
cd architect-insight-tools
git checkout develop
git add training/architect-insight-lora-final/
git commit -m "Add LoRA fine-tuned adapter weights"
git push origin develop
```

---

## Règles importantes

- ❌ **Ne ferme pas le navigateur** pendant l'entraînement
- ❌ **Ne laisse pas l'instance allumée** sans travailler (coûte des crédits AMD)
- ✅ **Coupe l'instance** dès que tu as récupéré le modèle fine-tuné
- ✅ **Partage le dossier** `architect-insight-lora-final/` via GitHub ou Hugging Face

---

## Contact

Si quelque chose ne marche pas, ouvre une issue sur GitHub ou contacte-moi directement.

---

*Document généré pour le AMD Developer Challenge 2026 — Projet ArchX*
