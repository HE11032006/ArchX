# ArchX — The Oracle of Stacks

> **Advanced AI-powered architectural analysis tool** — Analyzes any software repository and recommends the best architectural strategy (refactoring, migration, or status quo), powered by a fine-tuned Gemma model running on AMD MI300X.

---

## Table of Contents

1. [What is ArchX?](#what-is-archx)
2. [How it works — The Full Pipeline](#how-it-works)
3. [Project Structure](#project-structure)
4. [Quick Start](#quick-start)
5. [Dataset Generation](#dataset-generation)
6. [Fine-Tuning on AMD Cloud](#fine-tuning-on-amd-cloud)
7. [Frontend Dashboard](#frontend-dashboard)
8. [AMD Developer Challenge Context](#amd-developer-challenge-context)
9. [Contributing](#contributing)

---

## What is ArchX?

ArchX is a tool for software architects and engineering managers that analyzes the health of a codebase and provides **structured, AI-generated recommendations** on whether to:

- **Refactor** the existing codebase
- **Migrate** to a new tech stack
- **Maintain** the current architecture

Unlike generic AI assistants (ChatGPT, Claude, etc.), ArchX uses a **purpose-built, fine-tuned AI model** that has been specifically trained to reason about software architecture using real code metrics. This means its recommendations are:

- **Grounded in quantitative data** (coupling, cohesion, complexity, test coverage)
- **Structured and consistent** (always returns a valid JSON with a phased action plan)
- **Free from hallucinations** (trained with strict guard-rails: no invented ROI numbers, no $/€ costs)

---

## How it Works

ArchX is built around a **Teacher-Student Distillation** pipeline, a state-of-the-art technique in AI engineering:

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ARCHX PIPELINE                              │
│                                                                     │
│  1. COLLECT            2. GENERATE DATASET    3. FINE-TUNE          │
│  ─────────────         ──────────────────     ──────────────────    │
│  collector.py          generate_dataset.py    training/train_lora.py│
│  reads any Git repo    DeepSeek / GPT-4       Gemma 4B on AMD       │
│  and extracts:         (Teacher Model)        MI300X GPU (LoRA)     │
│                        ↓                      ↓                     │
│  - Coupling score      800 JSON examples      fine-tuned Gemma      │
│  - Cohesion score      (fr + en)              weights saved         │
│  - Complexity          training_data.jsonl    architect-insight-lora│
│  - Test coverage       ↓                                            │
│  - Anti-patterns       4. INFER               5. DISPLAY            │
│  - Git hotspots        ─────────────          ──────────────────    │
│  - Dependencies        The fine-tuned         React Dashboard       │
│  - Architecture        Gemma model            (ArchX frontend)      │
│    pattern             receives the           shows metrics +        │
│                        metrics as input       recommendation         │
│                        and outputs a          in a premium UI        │
│                        structured JSON                               │
└─────────────────────────────────────────────────────────────────────┘
```

### Why Fine-Tuning and not just GPT-4?

| | Generic LLM (GPT-4, Claude) | Fine-Tuned Gemma (ArchX) |
|---|---|---|
| **Cost per analysis** | ~$0.05–$0.20 | $0 (runs locally) |
| **Response format** | Inconsistent JSON | 100% valid JSON, always |
| **Knowledge** | General | Specialized in software architecture |
| **Privacy** | Code sent to 3rd party | Runs on your own infrastructure |
| **Speed** | ~3–10 seconds | <1 second on AMD MI300X |

---

## Project Structure

```
architect-insight-tools/
│
├── architect_insight/          # Core analysis engine (Python)
│   ├── collector.py            # Main entry point — scans a Git repo
│   ├── analyzers/              # Language-specific parsers
│   │   ├── dart_analyzer.py
│   │   ├── go_analyzer.py
│   │   ├── java_analyzer.py
│   │   ├── js_analyzer.py
│   │   ├── rust_analyzer.py
│   │   └── ...
│   └── metrics/                # Metric calculators
│       ├── architecture.py     # Detects patterns (MVC, Microservices, etc.)
│       ├── complexity.py       # Cyclomatic complexity
│       ├── cost_calculator.py  # Cloud cost estimation
│       ├── dependencies.py     # Dependency graph analysis
│       ├── git_hotspots.py     # Bug-prone files from Git history
│       ├── patterns.py         # Anti-pattern detection
│       └── tests.py            # Test coverage estimation
│
├── dataset_generation/         # AI Dataset pipeline
│   ├── generate_dataset.py     # Main script — calls DeepSeek/GPT via OpenRouter
│   ├── scenario_axes.py        # Generates diverse synthetic scenarios
│   ├── teacher_prompts.py      # Prompt templates for the Teacher model
│   └── training_data.jsonl     # ← Generated dataset (gitignored, ~159 examples)
│
├── training/                   # Fine-tuning scripts (run on AMD Cloud)
│   ├── train_lora.py           # LoRA fine-tuning with TRL + PEFT
│   ├── merge_adapter.py        # Merges LoRA weights into base model
│   └── format_for_training.py  # Converts JSON metrics → chat format
│
├── api/                        # FastAPI backend
│   ├── main.py                 # App entry point
│   ├── routes/                 # analyze, jobs, demo-projects, health
│   └── services/               # pipeline, job_store, health
│
├── frontend/                   # Next.js Dashboard (feature-based architecture)
│   ├── app/                    # App Router pages
│   │   ├── page.tsx            # Landing / scan
│   │   └── report/[jobId]/     # Architecture report
│   ├── features/
│   │   ├── scan/               # Scan form and preview
│   │   └── report/             # Report components
│   ├── shared/
│   │   ├── ui/                 # shadcn/ui components
│   │   ├── types/              # TypeScript domain types
│   │   └── data/               # Mock data for development
│   └── package.json
│
├── demo_projects/              # Sample repos used for demos
│   ├── django_app/
│   ├── spring_app/
│   └── flutter_app/
│
├── SETUP_AMD_CLOUD.md          # Step-by-step guide for AMD cloud setup
└── requirements.txt            # Python dependencies
```

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+ (for the frontend)
- Git

### 1. Clone and install dependencies

```bash
git clone <your-repo-url>
cd architect-insight-tools

# Python dependencies
pip install -r requirements.txt

# Frontend dependencies
cd frontend
npm install
cd ..
```

### 2. Configure environment variables

Create a `.env` file at the root (never commit this!):

```bash
# OpenRouter API key (for dataset generation only)
OPENROUTER_API_KEY=sk-or-v1-...
```

### 3. Run a demo analysis (CLI)

```bash
# Analyze a demo project via CLI
python demo.py --repo demo_projects/django_app --mock

# Or collect metrics only (no AI)
python -m architect_insight.collector demo_projects/django_app -o report.json
```

### 4. Start the API and frontend

```bash
# Terminal 1 — FastAPI backend
uvicorn api.main:app --reload --port 8000

# Terminal 2 — Next.js frontend
cd frontend
cp .env.local.example .env.local   # optional, defaults to localhost:8000
npm install
npm run dev
# → Open http://localhost:3000
```

Enter a demo slug (e.g. `django_app`) in the scan form to run a real analysis.

**Environment variables:**

| Variable | Location | Description |
|----------|----------|-------------|
| `ARCHX_MODEL_PATH` | root `.env` | Path to fine-tuned Gemma model (optional) |
| `ARCHX_MOCK_INFERENCE` | root `.env` | Force mock AI (`true`/`false`, optional) |
| `NEXT_PUBLIC_API_URL` | `frontend/.env.local` | API base URL (default: `http://localhost:8000`) |

---

## API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| `GET` | `/api/health` | Healthcheck |
| `GET` | `/api/demo-projects` | List available demo repositories |
| `POST` | `/api/analyze` | Start an analysis job |
| `GET` | `/api/jobs/{job_id}` | Poll job status and retrieve report |

Example:

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"repo": "django_app", "language": "fr"}'
```

---

## Dataset Generation

The dataset is what makes ArchX's AI "smart". It consists of **159 training examples** (+ 40 flagged for review) generated by a Teacher model (DeepSeek) that was given realistic software metrics and asked to write expert-level architectural recommendations.

```bash
# Dry run — tests the pipeline without API calls
python -m dataset_generation.generate_dataset --n 20 --dry-run

# Real generation (requires OPENROUTER_API_KEY)
python -m dataset_generation.generate_dataset \
    --n 100 --languages fr en \
    --out dataset_generation/training_data.jsonl \
    --review-out dataset_generation/to_review.jsonl \
    --model deepseek/deepseek-chat
```

**Key features of the pipeline:**
- **Checkpoint/Resume**: If interrupted (Ctrl+C or rate limits), re-running the same command resumes exactly where it left off.
- **Automatic retry**: On rate limit errors (429), the script waits and retries with fallback models.
- **Validation guard-rails**: Each generated example is validated — no invented costs ($/€), no hallucinated ROI numbers.
- **Bilingual**: Generates examples in both French and English.

---

## Fine-Tuning on AMD Cloud

This is the core technical contribution of the project. We fine-tune Google's **Gemma** model using **LoRA** (Low-Rank Adaptation) on an AMD **MI300X GPU** (192 GB VRAM) provided by the AMD Developer Cloud.

See the full step-by-step guide: [`SETUP_AMD_CLOUD.md`](SETUP_AMD_CLOUD.md)

**Summary of steps:**

```bash
# 1. On your local machine — push the dataset to the cloud instance
scp dataset_generation/training_data.jsonl user@amd-instance:~/

# 2. On the AMD cloud instance
pip install "transformers>=4.47" "trl>=0.12" "peft>=0.13" accelerate datasets

huggingface-cli login  # Required for Gemma (gated model)

python3 -m training.train_lora \
    --data dataset_generation/training_data.jsonl \
    --model google/gemma-4-12B-it \
    --output ./architect-insight-lora \
    --epochs 3

# 3. (Optional) Merge LoRA adapter into base model
python3 -m training.merge_adapter \
    --base google/gemma-4-12B-it \
    --adapter ./architect-insight-lora \
    --output ./architect-insight-merged
```

**Expected training time on MI300X:** ~2–4 hours for 3 epochs on 159 examples with a 12B model.

---

## Frontend Dashboard

The ArchX frontend is a **Next.js** application (App Router, TypeScript) with a **feature-based architecture**, Tailwind CSS, and shadcn/ui. It features a cyberpunk dark-mode design inspired by the "Oracle of Stacks" concept.

```bash
cd frontend
npm install
npm run dev   # Development server → http://localhost:3000
npm run build # Production build
```

**Features:**
- Hero landing page with repo URL input
- Live simulation of the analysis pipeline
- Metrics dashboard (coupling, complexity, test coverage)
- AI recommendation panel with phased action plan
- Risk assessment and cost analysis

---

## AMD Developer Challenge Context

This project was built for the **AMD Developer Challenge**, which provides participants with **$100 of free GPU credits** on the AMD Developer Cloud (MI300X instances with 192 GB VRAM).

The challenge requires demonstrating a meaningful use of AMD's GPU hardware. ArchX demonstrates:

1. **Data Engineering**: Automated, validated, bilingual dataset generation pipeline
2. **Fine-Tuning on AMD**: LoRA fine-tuning of Gemma on the MI300X using ROCm + PyTorch
3. **Real-World Application**: A practical tool with a full UI that solves a real engineering problem
4. **Teacher-Student Distillation**: A modern AI training technique (used by Meta, Google, OpenAI)

---

## Contributing

### Getting oriented

1. Read this README fully
2. Look at [`SETUP_AMD_CLOUD.md`](SETUP_AMD_CLOUD.md) to understand the full pipeline
3. Check the open tasks in the project

### Commit conventions

- Messages in **English**, no emojis
- Be descriptive but concise: `Add retry logic with exponential backoff to dataset generator`
- Never commit `.env` files or API keys

### Running tests

```bash
# Test the dataset validation pipeline (no API calls needed)
python -m dataset_generation.generate_dataset --n 10 --dry-run

# Test the collector on the demo projects
python prepare_demo_reports.py
```

---

*Built with ❤️ for the AMD Developer Challenge 2026*
