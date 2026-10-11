# Reproduce and submit the local prototype

Install Python dependencies from `requirements.lock.txt` and Node dependencies with `npm --prefix frontend ci`. Use the tested Python 3.14.7 and Node 26.8.2 environment; exact installed versions are recorded in the generated verification summary. See [reproducibility guide](reproducibility.md) for reference comparisons and environment isolation. From the repository root:

```sh
.venv/bin/python scripts/reproduce_submission.py
```

This regenerates the supplied snapshot model and synthetic impact model, prepares curated demo inputs, runs the held-out retrofit benchmark and arithmetic/runtime verification, Python tests, dependency checks, frontend tests/typecheck/build, then creates `submission/greenprint-team-254.zip`. Every command must exit zero. Detailed stdout/stderr logs and a machine-readable verification summary accompany the current evaluation report.

To package already verified artifacts without repeating checks:

```sh
.venv/bin/python scripts/build_submission.py
```

The ZIP contains source, tests, lockfiles, small synthetic datasets, generators, trained snapshot/impact models, methodology, current evaluation evidence, held-out predictions, label documentation and a SHA256 manifest. It excludes Git metadata, secrets, user SQLite data, dependencies, build outputs and historical reports. No large private/raw datasets need to enter Git. Generated ZIP/model binaries are ignored by Git; submit the ZIP as an artifact.

## Official deliverable mapping

| Requirement | Bundle content |
|---|---|
| A: working prototype | `frontend`, `backend`, `carbon_engine`, README local launch instructions |
| B: source/data/reproduction | `Data`, scripts, lockfiles, synthetic fixtures/provenance |
| C: trained models/inference | `ml/models/snapshot.joblib`, `ml/models/synthetic_impact.joblib`, inference modules |
| D: score mapping | `docs/scoring_methodology.md` |
| E: GenAI configuration/evaluation | advisor/LLM source, `docs/llm_methodology.md`, recorded advisor results and review sheet |
| F: architecture diagram | `docs/backend_architecture.md` |
| G: validation report | `docs/improvement_report.md`, selection/calibration/test metrics, verification summary |
| H: responsible AI | `docs/responsible_ai.md`, explicit synthetic/uncertainty warnings |
| I: held-out predictions/schema/labels | snapshot and impact predictions/splits, `evaluation/results/held_out_retrofits`, `docs/synthetic_impact_methodology.md` |

Only trusted, locally generated joblib files should be loaded: joblib uses pickle. Verification is synthetic/rule agreement, not observed-market or measured retrofit accuracy. Somyadeep's human explanation review remains pending until he fills the labels; packaging does not complete that review. Existing recorded advisor answers predate the new impact model and are marked historical evidence in the improvement report.

## Demo

Use `GREENPRINT_PROPERTY_DATASET=demo` when starting the backend. Select `DEMO-P00001`, assess, check recommendations, optimise £15,000 under carbon reduction, then compare with shortest payback. The comparison shows actual fuel/carbon/bill/payback tradeoffs and an explicitly synthetic value-impact range. Demonstrate missing critical inputs returning unavailable. Follow README for local Ollama or deterministic fallback.
