# Rapport de progression — ArchX

*Rédigé à partir de ce qui a été réellement observé pendant notre session de travail (migration Gemma, régénération du dataset, ajout de 5 features, débogage, déploiement). Franc et illustré, sans complaisance. Ce rapport distingue ce qui relève du **code pré-existant** (ton travail avant la session) de ce qui relève de tes **habitudes de travail** pendant la session.*

---

## 1. Points forts

**Tu challenges les décisions au lieu de suivre aveuglément.**
Quand tu voulais migrer vers Gemma 4 (première fois), tu m'as demandé explicitement *"TU DONNES UN AVIS POSITIF OU NÉGATIF À LA MIGRATION ?"*. Puis, face à mes réserves, tu as tranché toi-même *"oui laissons tomber gemma 4"* (à l'époque), avant d'y revenir plus tard une fois les contraintes réelles connues (192GB VRAM). C'est exactement la bonne posture : demander un avis argumenté, puis décider. Beaucoup de gens délèguent la décision entièrement.

**Tu as un vrai réflexe d'auto-critique produit.**
Ta question *"est-ce que ce projet est assez innovant ou trop léger ?"* n'est pas une question qu'on pose quand on veut se rassurer. Elle a débouché sur tout le travail de "raising the bar" (RLHF, simulateur, carte de dette). De même, quand je t'ai proposé le fix "band-aid" vs le fix "racine" du bug d'hallucination, tu as choisi la racine alors que c'était plus coûteux. C'est une maturité d'ingénieur.

**Tu testes en conditions réelles et tu partages les vrais outputs.**
Le bug d'hallucination le plus grave (le modèle inventait `.NET/ASP.NET/SQL Server` puis, plus tard, l'âge du projet et la composition junior/senior) n'a été trouvé **que** parce que tu as collé la sortie réelle du modèle fine-tuné au lieu de supposer que ça marchait. Sans ça, on aurait déployé un modèle qui hallucine. Tester le vrai artefact plutôt que le supposé, c'est une discipline précieuse.

**L'architecture de fond du projet est réfléchie.**
Trois choix pré-existants sont bons et je les ai constatés en lisant le code :
- Séparer le calcul de coût déterministe (`cost_calculator.py`) de l'inférence LLM — *"jamais générés par un LLM"* est écrit noir sur blanc. Beaucoup de projets laissent le LLM inventer des chiffres.
- Le pipeline teacher-student avec des "bandes de santé" (`scenario_axes.py`, 30/40/30 healthy/moderate/critical) pour éviter le biais "toujours réécrire".
- Le découplage collector → prompt → modèle → cost.

**Tu persévères.** Cette session a été un marathon de débogage (deprecations `trl`, chemins cassés, CORS, token leak, Vercel…). Tu n'as pas lâché.

---

## 2. Faiblesses techniques

**Du code qui n'a jamais été exécuté avant d'être commité.** *(exemple le plus parlant)*
`architect_insight/analyzers/java_analyzer.py` importait `from javaparser import JavaParser` — un paquet **qui n'existe pas sur PyPI**. Ton propre `requirements.txt` le disait déjà en commentaire (*"ce paquet n'existe pas sur PyPI sous ce nom, il fait planter pip"*). Résultat : `JAVA_AVAILABLE` était **toujours** `False`, et ta démo Spring Boot produisait des métriques vides — silencieusement. Un analyseur sur 9 était mort et personne ne l'avait remarqué parce qu'il échouait sans bruit. **Leçon : si un module n'a jamais fait planter un test, c'est souvent parce qu'aucun test ne l'exécute.**

**Des incohérences de clés entre producteur et consommateur.**
Le bug `duration_days_range` (string "15-20") vs `duration_days` (int) : le modèle produisait l'un, `pipeline.py` lisait l'autre → `migration_cost` valait toujours ~0 sur **100%** des analyses. Même famille de bug que `database` vs `database_name` (collision de clé qu'on a dû renommer partout). Ces bugs viennent d'un contrat de données implicite, jamais écrit ni vérifié. Il n'y avait **aucun test** dans le projet au départ (les 12 fichiers de `tests/` ont tous été créés pendant la session).

**Des garde-fous qui ne se déclenchaient jamais.**
`_MIGRATION_KEYWORDS` dans `generate_dataset.py` utilisait le radical `migrat` — qui ne matche jamais le verbe français "migrer" (seulement "migration"). Le garde-fou anti-biais healthy/critical était donc silencieusement inopérant sur une grande partie des exemples français. On l'a découvert en exécutant pour la première fois un script de test qui **dormait dans le repo sans jamais avoir été lancé** (`test_validation.py` n'avait pas de `sys.exit` sur échec, donc les échecs passaient inaperçus).

**Le désalignement train/production (le bug conceptuel central).**
C'est la faiblesse technique la plus importante et elle a mordu **deux fois**. `teacher_prompts.py` donnait au modèle-professeur l'âge du projet et le ratio junior/senior, en lui demandant de les *"intègre[r] naturellement"* dans la description. Mais en production, `collector.py` ne peut **jamais** fournir ces infos (elles n'existent pas dans un vrai scan de repo). Le modèle apprenait donc à énoncer des faits qu'il ne pourrait jamais connaître → hallucination systématique (~92% du dataset avant fix, mesuré). Le premier fix (la stack) a été fait plus tôt ; le deuxième (âge/équipe) n'avait **jamais** été corrigé et je l'ai trouvé pendant cette session. **Concept sous-jacent : train/serve skew — ton modèle doit être entraîné sur exactement la distribution d'entrées qu'il verra en production, ni plus, ni moins.**

**Gestion des chemins fragile.**
`api/config.py` chargeait `.env` via un chemin **relatif** (`env_file=".env"`). Lancer `uvicorn` depuis `training/` ne trouvait pas le `.env` à la racine → `ARCHX_MODEL_PATH` ignoré → repli silencieux en mode mock, **sans erreur visible**. Tu as cru que le modèle tournait alors qu'il renvoyait du mock. Même classe de problème que `DATASET_PATH = './training_data.jsonl'` dans le notebook, qui a planté parce que le fichier était dans `dataset_generation/`, pas à côté du notebook.

**Point transversal : trop d'échecs silencieux.** Java mort, `.env` non trouvé, garde-fous inertes, mode mock au lieu du vrai modèle — à chaque fois le système continuait comme si tout allait bien. Un bon système **crie** quand quelque chose ne va pas.

---

## 3. Failles de sécurité *(classées par gravité)*

### 🔴 CRITIQUE — Token Hugging Face commité dans le notebook
Au moment de `git push`, GitHub a bloqué le push (`GH013 / Push Protection`) en détectant un **vrai token HF valide** dans `training/finetune_lora_amd.ipynb:153`. Très probablement la **sortie d'une cellule** que tu avais exécutée en débogant (Jupyter sauvegarde les outputs dans le `.ipynb`). Sans le scanner automatique de GitHub, ce token partait en clair dans un repo. Statut : token révoqué pendant la session — **bien réagi**, mais c'était à un push près. **Un token HF avec droits d'écriture permet à quiconque de pousser du code malveillant sur tes modèles.**

### 🟠 ÉLEVÉ — Clés API réelles dans `.env.example`
Ton `.env.example` local contenait tes **vraies** clés (`OPENAI_API_KEY`, `GEMINI_API_KEY`, `MISTRAL_API_KEY`). Or `.env.example` est un **template versionné** dans git (contrairement à `.env`, correctement ignoré). Il n'était pas encore commité quand je l'ai repéré, mais il l'aurait été au prochain `git add`. Corrigé (remplacé par des placeholders), mais par prudence ces clés devraient être considérées comme potentiellement exposées et régénérées.

### 🟡 MOYEN — Secrets exposés sur de multiples surfaces
Au-delà des deux points ci-dessus, tes clés ont transité par : le fichier `.env` (que j'ai lu), les captures d'écran de terminaux, la conversation. Chaque surface est une fuite potentielle. Ce n'est pas une faille du code, mais une **hygiène** à resserrer : un secret qui apparaît quelque part en clair est un secret à considérer comme grillé.

### 🟡 MOYEN — Contournement de la vérification TLS
Sur Jupiter, on a utilisé `git -c http.sslVerify=false clone …` pour contourner une erreur de certificat. Je l'avais explicitement caveaté : acceptable sur une VM jetable pour du code public, **jamais** sur une machine manipulant des secrets. Le risque : un man-in-the-middle pourrait injecter du code. À ne pas transformer en habitude.

### 🟢 FAIBLE — CORS et surface d'API
`CORS_ORIGINS` a été correctement restreint à ton domaine Vercel (bien). Point de vigilance pour plus tard : l'endpoint `/api/analyze` clone des repos GitHub arbitraires fournis par l'utilisateur — en production ouverte, c'est une surface d'abus (SSRF, dépôts piégés, consommation disque). Le `ARCHX_CLONE_TIMEOUT`/`DEPTH` limite un peu, mais ça mériterait une validation d'URL plus stricte si l'app devient publique pour de vrai.

---

## 4. Habitudes de travail

**Tu lances des commandes sans vérifier où tu es.** *(le fil rouge de la session)*
- `python -m dataset_generation.generate_dataset` lancé **depuis** `dataset_generation/` → `ModuleNotFoundError`.
- Le dataset régénéré atterri à la **racine** du repo au lieu de `dataset_generation/` (chemins de sortie relatifs + mauvais répertoire de lancement).
- `uvicorn` lancé depuis `training/` → `.env` non trouvé → mode mock.
- `uvicorn: command not found` parce que lancé sans savoir quel environnement Python était actif.

À chaque fois, quelques minutes perdues. Le réflexe manquant : **`pwd` et `ls` avant une commande sensible au répertoire.**

**Tu ne comprenais pas toujours l'état du système que tu interrogeais.**
Tu as ré-interrogé **trois fois** le même `job_id` déjà terminé (`f3046634…`) en t'attendant à un résultat différent, alors que le job_store garde le résultat figé en mémoire. Il fallait créer un **nouveau** job. Comprendre qu'un GET sur une ressource terminée renvoie toujours la même chose (ce n'est pas un re-calcul) t'aurait évité de croire que le fix n'avait pas marché.

**Deux tunnels cloudflared tournaient en même temps** (PID 2463 **et** 2528), chacun avec une URL différente — d'où la confusion sur "quelle URL mettre dans Vercel". Symptôme d'un manque de suivi des process qu'on lance : on lance, ça marche, on oublie, on relance.

**Confusion sur le modèle mental de git.**
*"comment pull si je n'ai pas push"* — tu avais commité localement mais pas poussé, et l'articulation commit local / push / pull n'était pas nette. Puis le merge `test → develop → main` fait sans vérifier qu'il n'avait rien cassé. Git n'est pas encore un outil que tu manies avec confiance, et ça se voit dans les moments de stress (le push rejeté a généré de la friction).

**Le copier-coller casse ton code.**
`SyntaxError: unterminated string literal` — Jupyter avait coupé une chaîne trop longue au collage. Ce n'est pas ta faute directe, mais la parade (une clé/valeur par ligne, cellules courtes et isolées) est un réflexe à prendre quand on travaille dans un notebook distant.

**Ce qui est bien, en revanche :** quand tu partages une erreur, tu colles la **traceback complète**, pas juste "ça marche pas". C'est ce qui a permis de diagnostiquer vite. Garde ça.

---

## 5. Plan de progression

Pour chaque faiblesse importante, un concept concret à travailler.

| Faiblesse | Conseil actionnable | Concept / ressource |
|---|---|---|
| Token & clés exposés | Ne **jamais** taper un secret dans du code/une cellule/un terminal loggé. Toujours `os.environ.get()`. Installer un pre-commit hook `gitleaks` ou `detect-secrets` qui bloque un commit contenant un secret **avant** GitHub. | Chercher : *"git-secrets / gitleaks pre-commit hook"* ; concept de **secret scanning local**. |
| Désalignement train/prod (hallucinations) | Avant d'entraîner : lister ce que la **production** peut réellement fournir en entrée, et n'entraîner que là-dessus. Écrire un test qui compare les clés du prompt d'entraînement à celles du prompt de prod. | Concept ML clé : **train/serve skew** (biais entraînement/service). Lire la doc Google ML "Data and feature engineering → training-serving skew". |
| Code jamais exécuté / échecs silencieux | Règle : **tout module doit avoir au moins un test qui l'importe et l'exécute une fois.** Faire échouer bruyamment (`raise`, `logger.error`) au lieu de retourner un objet vide. | Concept : **fail-fast / fail-loud**. Exercice : ajouter un test "smoke" par analyseur de `architect_insight/analyzers/`. |
| Contrats de données implicites (`duration_days_range`, `database_name`) | Définir la forme des données échangées avec un schéma explicite (Pydantic, `TypedDict`, `dataclass`) au lieu de dicts libres, et valider aux frontières. | Concept : **schema-driven / parse, don't validate**. Tu utilises déjà Pydantic dans `api/schemas.py` — étends-le aux données internes. |
| Discipline de l'environnement d'exécution | Prendre le réflexe `pwd && ls` avant toute commande sensible au répertoire. Utiliser des **chemins absolus** dérivés du fichier (`Path(__file__).parent`) plutôt que relatifs — exactement le fix qu'on a appliqué à `config.py`. | Concept : **rendre le code indépendant du CWD**. Lancer les process longs dans `tmux`/`screen` pour ne pas les perdre. |
| Git sous stress | S'entraîner à froid sur le cycle `status → add → commit → push → pull` jusqu'à ce que le modèle mental soit automatique. Comprendre "local vs remote" comme deux dépôts distincts. | Ressource : *"Learn Git Branching"* (interactif, learngitbranching.js.org). |

---

## Les 3 priorités absolues pour la prochaine fois

**1. L'hygiène des secrets — parce que c'est la seule erreur de la liste aux conséquences irréversibles.**
Un bug de code se corrige ; un token poussé sur GitHub public est aspiré par des bots en minutes et peut coûter de l'argent réel ou compromettre tes modèles. Tu as eu de la chance que GitHub bloque le push. Installe un hook `gitleaks` cette semaine, et prends l'habitude de ne jamais laisser un secret apparaître en clair où que ce soit. **Coût pour toi : 30 minutes. Bénéfice : tu élimines toute une catégorie d'incidents.**

**2. Le désalignement entraînement/production — parce que c'est ton plus gros angle mort technique et qu'il t'a coûté deux retrains.**
Tu as vécu le même bug deux fois (stack, puis âge/équipe) sans reconnaître qu'ils étaient de la **même nature**. C'est le concept ML le plus important que cette session ait révélé chez toi. Internalise cette question avant chaque entraînement : *"Est-ce que chaque information dans ma sortie attendue est bien présente dans mon entrée réelle de production ?"* Si non, tu apprends à ton modèle à halluciner.

**3. La discipline de l'environnement d'exécution — parce que c'est ce qui t'a fait perdre le plus de temps en session.**
Répertoire courant, quel Python, quels process tournent, quelle URL est active : au moins la moitié des blocages de cette session venaient de là, pas du code. Ce ne sont pas des erreurs "intelligentes", ce sont des erreurs de **rigueur opérationnelle** — les plus faciles à éliminer, et celles qui font la différence entre un dev qui galère 3h et un qui déploie en 20 minutes. Réflexe à ancrer : `pwd`, `ls`, `ps aux | grep`, `git status`, **avant** d'agir.

---

*Bilan global honnête : le projet est réel, techniquement ambitieux, et tu as réussi à déployer un modèle fine-tuné fonctionnel de bout en bout — ce n'est pas rien. Mais une bonne partie de la difficulté de cette session ne venait pas du problème "difficile" (le fine-tuning), elle venait de la **rigueur de base** (chemins, secrets, contrats de données, tests). C'est une excellente nouvelle : ce sont précisément les compétences qui se travaillent le plus vite et qui te feront gagner le plus de temps.*
