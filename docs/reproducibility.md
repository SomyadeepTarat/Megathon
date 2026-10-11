# Reproduce GreenPrint AI / Kew

The tested environment is Python 3.14.7 and Node.js 26.8.2, recorded in `.python-version` and `.node-version`. These files document versions; they do not install runtimes. Other runtime versions are not verified by this reference run. Python package versions are fixed in `requirements.lock.txt`. Frontend direct dependencies and the complete dependency tree are pinned in `frontend/package.json` and `frontend/package-lock.json`.

## Fresh checkout

From the repository root, on Linux:

```sh
python3 --version
node --version
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
npm --prefix frontend ci
.venv/bin/python scripts/reproduce_submission.py
```

Use the tested runtime versions when comparing reference outputs. The initial dependency installation needs access to the Python and npm registries. Verification then uses local synthetic data, locally regenerated models and deterministic explanations; it does not require Ollama, credentials, a running web server, or a commercial LLM. The script checks installed Python versions against the lockfile and stops at the first failed step. Run `npm ci` before verification to install the locked frontend tree.

The command regenerates the snapshot model with seed 42 and the synthetic impact model with seed 254, prepares the curated demo, runs held-out retrofit evaluation, independent analytical reference cases, runtime verification, output repeatability checks, Python/frontend tests, dependency checks and a production frontend build. It creates `submission/greenprint-team-254.zip`, including trained models and a per-file SHA256 manifest, plus the ZIP checksum. It then extracts that ZIP into a different temporary directory and verifies its runtime reference outputs using the same installed Python environment. This catches missing runtime files such as SQLite migrations. This is local packaging; it does not commit, push or upload anything.

## Isolation and recorded evidence

Verification strips inherited `GREENPRINT_`, `VALUATION_`, `LLM_` and `OLLAMA_` settings and supplies documented settings itself. It fixes the Python hash seed and numerical-library thread counts. Tests use temporary SQLite databases, so developer edits in `backend/data/user_properties.db` cannot affect the reference ranking or alter a developer database. Demo provenance uses relative source paths rather than the original author's checkout location.

`evaluation/results/current_pipeline/submission_verification.json` records runtime versions, executed commands and exit codes, training seeds, Git commit and working-tree state, and hashes of lockfiles, input data, generated demo data, model artifacts, saved split manifests and reference outputs. Detailed logs are generated alongside it. The Git commit alone does not identify uncommitted edits; the working-tree flag and bundle file checksums expose that limitation. Commit the reviewed source and references before handing the repository to evaluators.

Property-group split manifests and held-out predictions are retained in `ml/reports/snapshot` and `ml/reports/synthetic_impact`. Existing methodology documents explain synthetic targets, baseline comparisons and limitations. Regenerated model binaries are ignored in Git and included in the submission bundle.

## Repeatability check

After generating the models, run:

```sh
.venv/bin/python -m evaluation.reproducibility
```

This launches two fresh Python processes, each with a separate empty SQLite database. It compares ten demo-property assessments and baseline valuations, the full property-ranking response, and three retrofit scenarios including unchanged baseline and interacting improvements. It checks input hashes against `evaluation/references/runtime_outputs.json` and compares numerical results with absolute tolerance 0.000001 and relative tolerance 0.000000001. Strings, ranks, classifications, nulls, row order and field structure must match exactly. Unsupported valuation inputs remain unavailable; they are preserved as reference outcomes rather than replaced with invented estimates.

A mismatch fails verification and reports its field path. Investigate changed inputs, code, package/runtime versions or model artifacts before accepting new references. This is regression evidence, not independent predictive validation. Independent analytical expectations remain in `evaluation.verify_reference_cases`, and held-out evaluation remains separate.

For an intentional, reviewed calculation or dataset change, first rerun the documented training and demo preparation commands, then explicitly refresh references:

```sh
.venv/bin/python -m evaluation.reproducibility --write-reference
.venv/bin/python scripts/reproduce_submission.py
```

Review the reference diff and evaluation metrics before committing them. Normal verification never rewrites the reference file. Do not refresh references just to hide a failure.

## Scope and limits

The supported target is repeatable numerical outputs with documented tolerance, not identical binary model files or identical ZIP bytes across operating systems. Floating-point libraries can differ across platforms. Checksums identify the artifacts used in each run; a changed checksum must be investigated but does not alone prove changed predictions.

Deterministic explanations are used for the reference workflow. External Ollama/LLM responses and model downloads are not guaranteed identical across runs; their numerical facts still come from backend calculations. Human groundedness/accuracy evaluation requires completed independent review labels. Synthetic reference agreement does not establish real-world energy accuracy, market valuation accuracy, or a causal retrofit premium.

The reference ranking is calculated from versioned demo inputs. Interactive edits persist separately in SQLite and intentionally change results. To reproduce an edited property, retain its exact input snapshot and the calculation/model configuration. The current recorded valuation is a supplied dataset baseline, not a live market feed.
