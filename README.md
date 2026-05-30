# Zomoto — AI-Powered Restaurant Recommendations

Zomato-inspired restaurant recommendation service that combines structured Zomato data with an LLM for personalized, explainable suggestions.

## Documentation

| Document | Description |
|----------|-------------|
| [`docs/context.md`](docs/context.md) | Product context and success criteria |
| [`docs/architecture.md`](docs/architecture.md) | System design and components |
| [`docs/implementation-plan.md`](docs/implementation-plan.md) | Phase-wise build plan |
| [`docs/edge-cases.md`](docs/edge-cases.md) | Edge cases and failure handling |

## Requirements

- Python **3.11+**
- (Phase 3+) [Groq API key](https://console.groq.com/keys) (`GROQ_API_KEY`)

## Setup

```bash
# Clone and enter the project
cd zomoto

# Create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Optional: editable install with pyproject.toml
pip install -e ".[dev]"

# Configure environment
copy .env.example .env   # Windows
# cp .env.example .env   # macOS / Linux
# Edit .env and set GROQ_API_KEY for AI recommendations
```

## Environment variables

See [`.env.example`](.env.example). Key variables:

| Variable | Description |
|----------|-------------|
| `HF_DATASET_NAME` | Hugging Face dataset id (default: Zomato recommendation dataset) |
| `LLM_PROVIDER` | `groq` (only supported provider in v1) |
| `LLM_MODEL` | Groq model (default: `llama-3.3-70b-versatile`) |
| `GROQ_API_KEY` | Groq API key (or `LLM_API_KEY` alias) |
| `MAX_CANDIDATES` | Max restaurants sent to the LLM (default: 30) |
| `TOP_K` | Final recommendation count (default: 5) |
| `BUDGET_BANDS` | JSON cost bands for low / medium / high |

## Run tests

```bash
python -m pytest
```

Live Groq test (optional):

```bash
set RUN_GROQ_INTEGRATION=1
set GROQ_API_KEY=your_key
python -m pytest tests/test_llm_integration.py -v
```

Tests use in-memory fixtures by default (no Hugging Face download). To inspect the live dataset after install:

```bash
python scripts/inspect_dataset.py
python scripts/inspect_dataset.py --limit 10
```

## Run the app

Streamlit UI (Phase 5) lets you submit preferences and view top recommendations.

```bash
streamlit run src/app/main.py
```

## Project layout

```text
zomoto/
├── config/settings.py      # Environment-backed settings
├── src/
│   ├── data/               # Phase 1: dataset load & repository
│   ├── models/             # Phase 2: Pydantic domain models
│   ├── services/           # Phases 2–3: filter & LLM
│   ├── orchestration/      # Phase 4: recommend() pipeline
│   └── app/                # Phase 5: Streamlit UI
├── tests/
└── docs/
```

## Implementation status

- [x] **Phase 0** — Project foundation, config, tests, Streamlit shell
- [x] **Phase 1** — Data ingestion (loader, preprocessor, repository)
- [x] **Phase 2** — Domain models & filter layer
- [x] **Phase 3** — Groq LLM recommendation engine
- [x] **Phase 4** — Orchestration (end-to-end recommend() pipeline + CLI)
- [x] **Phase 5** — User input & output display (Streamlit UI)
- [x] **Phase 6** — Testing & hardening
- [ ] Phase 7 — Deployment (optional)

## Run the recommendation pipeline (CLI)

Phase 4 provides a CLI that runs the full flow: load → filter → (Groq or fallback) → merge.

```bash
python -m src.cli --location Bangalore --budget medium --cuisine Italian --min-rating 4.0 --additional "family-friendly"
```

Notes:
- Logs go to stderr; JSON result goes to stdout.
- If `GROQ_API_KEY` / `LLM_API_KEY` is not set, the pipeline automatically falls back to rating-based ranking.

## Run the backend (FastAPI)

```bash
uvicorn src.api.main:app --reload --port 8000
```

- Health: `http://localhost:8000/api/v1/health`
- API docs: `http://localhost:8000/docs`

## Manual testing (Phase 6)

See: `docs/manual-testing-phase6.md`

## Known Limitations

1. **Neighborhood-based City Names**: In the Zomato Bangalore dataset, the location column stores local neighborhoods (e.g. `Indiranagar`, `BTM`, `Basavanagudi`, `Whitefield`) rather than the city name `Bangalore`. Users of the app or CLI must query for these specific neighborhoods. Querying for the parent city `"Bangalore"` directly yields an empty candidate list (`NO_LOCATION_MATCH`).
2. **Deterministic Candidate Capping**: Before prompting the LLM, candidate restaurants are filtered and capped to `MAX_CANDIDATES` (default: 30) sorted by rating and vote count. Only these top candidates are sent to the LLM for ranking to control token usage and latency.
3. **In-Memory Store**: The database is fully cached in-memory at application startup, which provides sub-millisecond filtering performance but requires sufficient RAM to load the dataset.

## License

See repository owner for license terms.
