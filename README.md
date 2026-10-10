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
| GET /properties | Three labeled synthetic development homes |
| GET /properties/{id} | Validated property and annual energy snapshot |
| GET /properties/{id}/assessment | Score components and issues |
| POST /assessments | Assessment of a supplied or edited snapshot |
| POST /scenarios/simulate | Orchestration through dependency-injected engines |

Demo homes intentionally have no benchmark. Full score is unavailable until a documented applicable benchmark is supplied; known component subscores remain visible. No invented official benchmark is bundled. Benchmark source authenticity is not verified by Pydantic: P3 must provide a trusted repository.

Default scenario responses are HTTP 503 with baseline assessment and explicit unavailable results while P4's engine is absent. Rejected or conditional packages use HTTP 409; completed simulations use HTTP 200 with success or partial status. Numerical test adapters are confined to tests and never installed in runtime routes. The existing valuation adapter disables illustrative synthetic-model uplift by default.

See [backend handoff](docs/backend_handoff.md), [scoring methodology](docs/scoring_methodology.md), and [architecture](docs/backend_architecture.md). Existing teammate implementation and documentation are preserved below.

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
