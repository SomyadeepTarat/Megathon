# GreenPrint AI

FastAPI backend, explainable scoring, teammate integration contracts, property fixtures, and the existing Person 5 valuation/evaluation module.

## Backend setup on Omarchy

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.lock.txt
python -m uvicorn app.main:app --app-dir backend --reload --port 8001
```

Open http://localhost:8001/docs. Stop the old server using port 8001 before starting this checkout. Configuration is read from shell environment variables; `.env.example` is a template, not automatically loaded.

For the exact combined dependency snapshot and the complete test suite:

```bash
pip install -r requirements.lock.txt
python -m pytest -q
```

For backend-only verification:

```bash
python -m pytest backend/tests -q
```

## Available API

| Route | Behavior |
|---|---|
| GET /health | Implementation status |
| GET /properties | 100 synthetic homes from the teammate CSV dataset |
| GET /properties/{id} | Validated property and annual energy snapshot |
| GET /properties/{id}/assessment | Score components and issues |
| POST /assessments | Assessment of a supplied or edited snapshot |
| POST /scenarios/simulate | Orchestration through dependency-injected engines |
| POST /advisor/chat | Grounded explanations of server-owned results; explicit partial/unavailable status |

The CSV dataset intentionally has no scoring benchmark. Full score is unavailable until a documented applicable benchmark is supplied; known component subscores remain visible. No invented official benchmark is bundled. Benchmark source authenticity is not verified by Pydantic: P3 must provide a trusted repository.

The real P4 adapter is connected. Scenarios require confirmed eligibility, sufficient physical inputs, and documented fuel factors; missing dependencies return HTTP 503 with a reason. Rejected or conditional packages use HTTP 409; completed simulations use HTTP 200 with success or partial status. Numerical test adapters are confined to tests and never installed in runtime routes. The existing valuation adapter disables illustrative synthetic-model uplift by default.

The API defaults to `Data/csv/properties.csv` and `Data/csv/energy_usage.csv`. Complete annual consumption is the sum of twelve monthly readings per fuel. Missing fuel coverage produces null annual totals. Set `GREENPRINT_PROPERTY_DATASET=fixtures` to select the original three development homes. Generic heat-pump subtype and solar contribution stay unknown when the CSV does not provide them. See [dataset integration](docs/dataset_integration.md).

See [backend handoff](docs/backend_handoff.md), [scoring methodology](docs/scoring_methodology.md), and [architecture](docs/backend_architecture.md). Existing teammate implementation and documentation are preserved below.

## Local AI advisor (Person 2)

The advisor is mounted in the existing backend. Without an LLM it uses deterministic
explanations. For local Ollama, start its server, ensure `qwen3:4b` is already installed,
and set `LLM_PROVIDER=ollama`, `LLM_MODEL=qwen3:4b` before starting the backend.
The adapter disables thinking and enforces task-specific JSON output schemas.

Use `/docs` to call `/advisor/chat` with a property ID from `/properties` and a message
such as `Explain my score`. Verified partial evidence remains visible when the full
score or valuation is unavailable. What-if requests report unavailable while P4's
runtime engine is pending; budget optimization is also pending. Negated/comparison
requests require explicit full package selection. Frontend implementation is deferred.
See [AI advisor methodology and integration](docs/llm_methodology.md) for request examples,
PowerShell settings and limitations.

---

# GreenPrint AI — Person 5 module

Valuation ML, conservative uncertainty, backend inference and evaluation tooling from `prd.md`. Other team members' engines are not implemented here.

## Reproduce

Run from the repository root with Python 3.11+:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r ml/requirements.txt
.venv/bin/python -m ml.make_fixture
.venv/bin/python -m ml.train_valuation --data ml/fixtures/synthetic_sales.csv --provenance ml/fixtures/provenance.json
.venv/bin/python -m pytest ml/tests evaluation/tests -q
.venv/bin/python -m ml.demo_valuation
```

This generates a **synthetic demonstration model**, `ml/models/valuation.joblib`, metrics, held-out predictions and a split manifest in `ml/reports/`. The binary is ignored by Git; reproduce it using these commands. Replace the fixture paths with Person 3's audited observed data and provenance to train a real-data model. Do not describe fixture metrics as market accuracy.

External evaluation rejects IDs present in the original training/calibration/test manifest:

```sh
.venv/bin/python -m ml.evaluate_valuation --model ml/models/valuation.joblib --data PATH_TO_NEW_SALES.csv --manifest ml/reports/split_manifest.csv
.venv/bin/python -m evaluation.test_scenarios --input PATH_TO_RECORDED_SCENARIOS.json
.venv/bin/python -m evaluation.evaluate_recommendations --input PATH_TO_REVIEWED_LABELS.json
.venv/bin/python -m evaluation.evaluate_energy --input PATH_TO_INDEPENDENT_ENERGY_REFERENCES.json
.venv/bin/python -m evaluation.evaluate_explanations --input PATH_TO_RECORDED_RESPONSES.json
```

Read [the walkthrough](docs/person5_walkthrough.md), [the data and backend handoff](docs/valuation_methodology.md), [evaluation status](docs/evaluation_report.md) and [responsible AI note](docs/responsible_ai.md). `evaluation/explanation_cases.json` contains 25 questions awaiting actual responses and reviewer labels. The evaluator must receive recorded responses, not this unfilled template. Exact versions used for the recorded run are in `ml/requirements-lock.txt`; the broader requirements support other compatible Python installations.


## Person 1 runtime integration

The production routes call the contributed carbon_engine through a typed adapter. POST /retrofits/recommend screens individual feasible measures; it does not promise package optimization. POST /properties/{id}/valuation exposes the existing P5 service. POST /assessments/full returns baseline assessment, energy, carbon and valuation statuses together. GET /health includes readiness requirements; process liveness does not imply complete calculations.

Provide physical inputs under property.physical_inputs, preserving per-field source metadata. solar_installed, heat_pump_installed and loft_insulation_installed are explicit optional booleans. Unsupported heat-pump subtype, renewable contribution and projected EPC remain unknown. Installation costs may be supplied as documented retrofit_costs; missing costs are null and cannot prove budget compliance.

Supply emission_factors in the request or set GREENPRINT_EMISSION_FACTORS_FILE to a documented factor JSON containing electricity and gas records, each with fuel, kg_co2e_per_kwh, source, source_year, accounting_boundary and version. No invented factors are bundled. Factor metadata is operator-supplied; the API validates shape, not source authenticity. To use the advisor with those factors and edited inputs, register the snapshot with POST /properties first. Registered snapshots are kept in memory until restart.

See docs/person1_runtime_integration.md for contracts, verification and remaining teammate dependencies.
