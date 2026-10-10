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
