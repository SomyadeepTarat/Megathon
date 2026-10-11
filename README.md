# GreenPrint AI / Kew

Local Next.js frontend, FastAPI backend, SQLite property snapshots, deterministic scoring/retrofit/carbon engines, guarded valuation ML and grounded AI explanations. Requirements: [prd.md](prd.md). Current verification and remaining evidence gaps: [pipeline report](evaluation/results/current_pipeline/README.md). Older reports are historical snapshots, not current readiness statements.

## Install and prepare

The reference environment is Python 3.14.7 and Node.js 26.8.2. See [reproducibility guide](docs/reproducibility.md) for fresh-checkout setup, isolated verification and reference-output comparisons. Run from the repository root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
npm --prefix frontend ci
.venv/bin/python -m ml.train_valuation --data Data/csv/properties.csv --provenance ml/snapshot_provenance.json --target-kind snapshot --output ml/models/snapshot.joblib --reports ml/reports/snapshot
.venv/bin/python -m ml.synthetic_impact
.venv/bin/python scripts/prepare_demo.py
npm --prefix frontend run build
```

Model binaries, SQLite databases, dependencies and build output are ignored by Git. The supplied 100 homes and 1,200 monthly readings are **synthetic**. Snapshot-model metrics measure fit to synthetic baseline estimates, not real sale prices or retrofit premiums. For the separate synthetic sales experiment:

```sh
.venv/bin/python -m ml.make_fixture
.venv/bin/python -m ml.train_valuation --data ml/fixtures/synthetic_sales.csv --provenance ml/fixtures/provenance.json --reports ml/reports/sales
.venv/bin/python -m ml.demo_valuation
```

## Run the London demo

Prepare the 1,900 fresh London simulations and frozen Ridge baseline first:

```sh
.venv/bin/python scripts/prepare_london_demo.py
```

The original 100 are retained only as diagnostics. The active model uses price-proportional calibrated ranges. Prices and properties remain synthetic; published aggregate references are not matched transactions. Compatibility, cost and tariff gaps remain explicit.

## Start services

In one terminal, from the repository root:

```sh
GREENPRINT_PROPERTY_DATASET=london .venv/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8001
```

In a second terminal:

```sh
npm --prefix frontend start -- --port 3000
```

Open http://127.0.0.1:3000; API documentation is at http://127.0.0.1:8001/docs. The backend automatically loads the project-root `.env`; shell variables take precedence. Configure `LLM_PROVIDER=groq`, `GROQ_API_KEY` and `GROQ_MODEL` for hosted AI. `LLM_FALLBACK_PROVIDER=ollama` and `OLLAMA_MODEL=qwen3:4b` keep local Ollama as backup at http://127.0.0.1:11434. Rate limits, provider errors and malformed Groq responses trigger Ollama; if that also fails, verified deterministic explanations remain available. Set `LLM_PROVIDER=deterministic` to disable model calls. Both providers use the same system prompts and numerical grounding checks. The key belongs only in the ignored `.env`, never frontend configuration.

`GREENPRINT_PROPERTY_DATASET=london` (default) selects only the 1,900 fresh London properties and `ml/models/london_snapshot.joblib`. `csv` explicitly selects the legacy 100 supplied homes. `demo` selects 10 curated synthetic variants with clearly labelled suitability, proposed system, cost and tariff assumptions; it never modifies the supplied CSVs. `fixtures` selects three original development examples. London edits persist separately in `backend/data/london_user_properties.db`; legacy profiles use `backend/data/user_properties.db`. Override with `GREENPRINT_DB_PATH`.

Demo sequence: select `DEMO-P00001` → run assessment → retrofit planner → choose measures or optimize a £15,000 budget → compare fuel, carbon, bills and payback → ask the advisor. Complete supported synthetic scenarios show an illustrative value-impact range; missing or unsupported inputs remain explicitly unavailable. Conditional/infeasible measures are not simulated or recommended as confirmed installations.

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
| GET /properties/ranking; GET /portfolio/rank | Complete feasible-package improvement potential; unavailable stays null |
| POST /advisor/chat | Fresh backend calculations followed by fact selection or deterministic explanation |

Scores use PRD weights and mappings; unknown fields stay unknown. Annual energy requires all 12 monthly readings per fuel. Envelope/controls changes affect space heating; hot water and appliance loads are retained. Heat pumps preserve signed electricity/gas changes, and solar reduces grid imports. Financial outputs require supplied cost sources and tariffs. Missing dependencies/physical inputs are explicit, not invented zeroes.

The default carbon factors are extracted from the corrected 2026 DESNZ flat workbook. [Factor provenance](Data/csv/emission_factors_2026.provenance.json) records exact workbook IDs, source URL, SHA256, accounting boundaries and licence. Electricity is UK location-based generation; gas is direct combustion on a gross-calorific basis. Upstream and transmission/distribution emissions are excluded. Set `GREENPRINT_EMISSION_FACTORS_FILE` to a documented CSV/JSON, or explicitly empty to disable carbon. To reproduce extraction from the official downloaded workbook:

```sh
.venv/bin/python scripts/extract_emission_factors.py --help
```

Valuation selects the simplest validated model against Ridge/HistGradientBoosting alternatives, uses property-group separation and held-out conformal calibration, and checks input support. Complete explicitly synthetic scenarios use an illustrative intensity-based impact model with paired calibration; observed inputs retain strict evidence guards. New EPC estimates and causal premiums are never fabricated. Solar contribution and whole-home insulation categories remain unknown/unchanged without a supported category estimator, so some after-scenario full scores are unavailable even when fuel/carbon calculations work.

Methodology: [scoring](docs/scoring_methodology.md), [valuation](docs/valuation_methodology.md), [advisor](docs/llm_methodology.md), [responsible AI](docs/responsible_ai.md). External evaluators require documented reference labels or independent reviewed inputs, not unfilled templates: `evaluation.evaluate_energy`, `evaluation.evaluate_recommendations`, `evaluation.evaluate_explanations`, `ml.evaluate_valuation` (each provides `--help`).

## Synthetic-demo acceptance

Synthetic data is the agreed hackathon scope. Observed-market and measured retrofit validation remain future work. Numerical implementation checks can be reproduced with `.venv/bin/python -m evaluation.verify_reference_cases`; fixed analytical expectations are not measured predictive accuracy. Desktop/mobile browser smoke testing is recorded in the current pipeline report.

Somyadeep's [25-answer review](evaluation/reviews/somyadeep.md) is ready. Fill the true/false judgements in [the JSON review](evaluation/reviews/somyadeep.json), then run `.venv/bin/python -m evaluation.evaluate_explanations --input evaluation/reviews/somyadeep.json`. Pending human labels remain null; human quality targets have not been claimed.

## Submission and expanded evaluation

Run `.venv/bin/python scripts/reproduce_submission.py` to regenerate models, verify the pipeline and create the team-254 ZIP with trained artifacts and checksums. See [submission guide](docs/submission_guide.md), [current improvement report](docs/improvement_report.md), and [synthetic impact methodology](docs/synthetic_impact_methodology.md). The separate property-ranking page shows backend improvement-potential ranks and recorded current valuations. Individual recommendations retain suitability; optimised comparisons show the carbon/energy/payback winners for the same budget.

London verification: `.venv/bin/python -m evaluation.verify_london_workflow` (set `LLM_PROVIDER=ollama LLM_MODEL=qwen3:4b` for local AI). See `evaluation/results/london_active/README.md` for current workflow evidence, arbitrary edited inputs, missing/conflicting cases and limitations. Property tables paginate in groups of 50; search and export operate across the complete result set.


## Static data documentation

The data relationships, formulas, label generation, quality, validation and reproducibility are documented in [Data/index.html](Data/index.html), with a clickable section index. The page uses local CSS and works without JavaScript or a network connection. Its maintained source is [README_DATA_METHODOLOGY.md](Data/README_DATA_METHODOLOGY.md).

Open the HTML file directly, or serve the repository root:

```sh
python -m http.server 8080 --bind 127.0.0.1
```

Then open [the data documentation](http://127.0.0.1:8080/Data/index.html). Serving from the repository root also makes linked reports and source files available.

After editing the methodology source, regenerate the static page:

```sh
python Data/scripts/build_documentation.py
```

These documentation commands use only Python's standard library. No externally hosted Kew/documentation URL is recorded here.

### Persistent customer memory

Kew's **What Kew remembers** panel saves budgets, priorities, unwanted upgrades, completed work and package feedback in SQLite. Saved choices adapt fresh engine calculations across reloads and server restarts. See [customer memory guide](docs/customer_memory.md) for the workflow, consistency safeguards, verification and deployment limitations.
