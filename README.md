# GreenPrint AI / Kew

Local Next.js frontend, FastAPI backend, SQLite property snapshots, deterministic scoring/retrofit/carbon engines, guarded valuation ML and grounded AI explanations. Requirements: [prd.md](prd.md). Current verification and remaining evidence gaps: [pipeline report](evaluation/results/current_pipeline/README.md). Older reports are historical snapshots, not current readiness statements.

## Install and prepare

Run from the repository root with Python 3.11+ and Node.js 22+:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
npm --prefix frontend ci
.venv/bin/python -m ml.train_valuation --data Data/csv/properties.csv --provenance ml/snapshot_provenance.json --target-kind snapshot --output ml/models/snapshot.joblib --reports ml/reports/snapshot
.venv/bin/python scripts/prepare_demo.py
npm --prefix frontend run build
```

Model binaries, SQLite databases, dependencies and build output are ignored by Git. The supplied 100 homes and 1,200 monthly readings are **synthetic**. Snapshot-model metrics measure fit to synthetic baseline estimates, not real sale prices or retrofit premiums. For the separate synthetic sales experiment:

```sh
.venv/bin/python -m ml.make_fixture
.venv/bin/python -m ml.train_valuation --data ml/fixtures/synthetic_sales.csv --provenance ml/fixtures/provenance.json --reports ml/reports/sales
.venv/bin/python -m ml.demo_valuation
```

## Run the demo

In one terminal, from the repository root:

```sh
GREENPRINT_PROPERTY_DATASET=demo LLM_PROVIDER=ollama LLM_MODEL=qwen3:4b .venv/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8001
```

In a second terminal:

```sh
npm --prefix frontend start -- --port 3000
```

Open http://127.0.0.1:3000; API documentation is at http://127.0.0.1:8001/docs. Ollama must already be serving at http://127.0.0.1:11434 with the selected model installed. Omit `LLM_PROVIDER` and `LLM_MODEL` for deterministic explanations. Provider errors also fall back to verified facts. Configuration is read from shell variables; `.env.example` is not automatically loaded by the backend.

`GREENPRINT_PROPERTY_DATASET=csv` (default) selects all 100 supplied homes. `demo` selects 10 curated synthetic variants with clearly labelled suitability, proposed system, cost and tariff assumptions; it never modifies the supplied CSVs. `fixtures` selects three original development examples. Edited/API-submitted snapshots persist in `backend/data/user_properties.db`; override with `GREENPRINT_DB_PATH`.

Demo sequence: select `DEMO-P00001` → run assessment → retrofit planner → choose measures or optimize a £15,000 budget → compare fuel, carbon, bills and payback → ask the advisor. Property-value impact remains explicitly unavailable where evidence does not support it. Conditional/infeasible measures are not simulated or recommended as confirmed installations.

## Verification

```sh
.venv/bin/python -m pytest -q
.venv/bin/python -m pip check
npm --prefix frontend run typecheck
npm --prefix frontend test
npm --prefix frontend run build
.venv/bin/python -m evaluation.evaluate_initial_dataset --output evaluation/results/current_dataset
.venv/bin/python -m evaluation.verify_runtime
.venv/bin/python -m evaluation.audit_full_pipeline --ollama --model qwen3:4b --timeout 20
```

With the servers running, append `--frontend-url http://127.0.0.1:3000` to `evaluation.verify_runtime` to verify production pages and the backend proxy. The runtime verifier exercises 100 assessments and 10 curated homes × three objectives × 32 package decisions using production adapters. The advisor audit records 25 actual responses; human review fields remain unfilled until independently reviewed. It does not claim the PRD's human accuracy thresholds are met.

Data regeneration works from any working directory and preserves the enriched columns:

```sh
.venv/bin/python Data/scripts/generate_properties.py --output /tmp/properties.csv
.venv/bin/python Data/scripts/generate_energy_usage.py --output /tmp/energy_usage.csv
```

The property generator preserves contributed physical fields only when they match the reproducible base homes; it rejects stale enrichment rather than assigning it to different generated homes.

## API and calculation rules

| Route | Behavior |
|---|---|
| GET /health | Liveness and calculation readiness |
| GET /properties; GET /properties/{id} | Validated property snapshots |
| POST /properties | Persist an edited snapshot, including documented costs/tariffs |
| GET /properties/{id}/assessment; POST /assessments | Seven-component weighted Green Home Score and issues |
| POST /assessments/full | Score, energy, sourced baseline carbon and impact availability |
| GET or POST /properties/{id}/valuation | Illustrative/indicative baseline estimate with calibrated range |
| POST /properties/{id}/valuation/impact | Guarded value-impact estimate; critical missing fields return nulls and a reason |
| POST /scenarios/simulate | Confirmed-feasible, sequential retrofit simulation |
| POST /retrofits/recommend | Feasibility and objective-ranked individual measures |
| POST /retrofits/optimize | All 32 subsets; explicit budget, documented costs and objective |
| GET /portfolio/rank | Complete feasible-package improvement potential; unavailable stays null |
| POST /advisor/chat | Fresh backend calculations followed by fact selection or deterministic explanation |

Scores use PRD weights and mappings; unknown fields stay unknown. Annual energy requires all 12 monthly readings per fuel. Envelope/controls changes affect space heating; hot water and appliance loads are retained. Heat pumps preserve signed electricity/gas changes, and solar reduces grid imports. Financial outputs require supplied cost sources and tariffs. Missing dependencies/physical inputs are explicit, not invented zeroes.

The default carbon factors are extracted from the corrected 2026 DESNZ flat workbook. [Factor provenance](Data/csv/emission_factors_2026.provenance.json) records exact workbook IDs, source URL, SHA256, accounting boundaries and licence. Electricity is UK location-based generation; gas is direct combustion on a gross-calorific basis. Upstream and transmission/distribution emissions are excluded. Set `GREENPRINT_EMISSION_FACTORS_FILE` to a documented CSV/JSON, or explicitly empty to disable carbon. To reproduce extraction from the official downloaded workbook:

```sh
.venv/bin/python scripts/extract_emission_factors.py --help
```

Valuation selects the simplest validated model against Ridge/HistGradientBoosting alternatives, uses property-group separation and held-out conformal calibration, and checks input support. Synthetic uplift is disabled in production. New EPC estimates and causal premiums are never fabricated. Solar contribution and whole-home insulation categories remain unknown/unchanged without a supported category estimator, so some after-scenario full scores are unavailable even when fuel/carbon calculations work.

Methodology: [scoring](docs/scoring_methodology.md), [valuation](docs/valuation_methodology.md), [advisor](docs/llm_methodology.md), [responsible AI](docs/responsible_ai.md). External evaluators require actual reviewed inputs, not unfilled templates: `evaluation.evaluate_energy`, `evaluation.evaluate_recommendations`, `evaluation.evaluate_explanations`, `ml.evaluate_valuation` (each provides `--help`).
