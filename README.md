# Kew â€” setup and run

Requirements: Python **3.11+**, Node.js **22+**, and npm. Run commands from the repository root. Dependencies use the committed lock files.

## Setup

Windows PowerShell:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.lock.txt
npm --prefix frontend ci
.venv/Scripts/python.exe -m ml.train_valuation --data Data/csv/properties.csv --provenance ml/snapshot_provenance.json --target-kind snapshot --output ml/models/snapshot.joblib --reports ml/reports/snapshot
.venv/Scripts/python.exe -m ml.synthetic_impact
.venv/Scripts/python.exe scripts/prepare_demo.py
npm --prefix frontend run build
```

On macOS/Linux, use `python3 -m venv .venv` and replace `.venv/Scripts/python.exe` with `.venv/bin/python` in the commands above and below.

## Run locally

Start the backend in one PowerShell terminal:

```powershell
$env:GREENPRINT_PROPERTY_DATASET='demo'
.venv/Scripts/python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8001
```

On macOS/Linux, the equivalent backend command is:

```sh
GREENPRINT_PROPERTY_DATASET=demo .venv/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8001
```

Start the frontend in a second terminal:

```sh
npm --prefix frontend start -- --port 3000
```

Open [Kew](http://127.0.0.1:3000) and [API documentation](http://127.0.0.1:8001/docs). For frontend development, use `npm --prefix frontend run dev -- --port 3000` instead of `start`.

`demo` loads the ten curated synthetic homes; `csv` loads the original hundred. Set environment variables in the launching shell; the backend does not automatically load `.env.example`. The frontend proxies to `http://127.0.0.1:8001`; set `GREENPRINT_BACKEND_URL` before building if that address changes. User edits persist in `backend/data/user_properties.db`; override using `GREENPRINT_DB_PATH`.

Optional local AI: install [Ollama](https://ollama.com/), run `ollama pull qwen3:4b`, and ensure it serves at `http://127.0.0.1:11434`. Set `LLM_PROVIDER=ollama` and `LLM_MODEL=qwen3:4b` in the backend shell. Without these variables, explanations use the deterministic fallback.

## View the static data documentation

Open [Data/index.html](Data/index.html) directly in a browser, or serve the repository in a third terminal:

```powershell
.venv/Scripts/python.exe -m http.server 8080 --bind 127.0.0.1
```

Open [the data methodology page](http://127.0.0.1:8080/Data/index.html). Serving from the repository root also makes linked reports and implementation files accessible. No externally hosted Kew or documentation URL is currently recorded in this repository.

After editing [the methodology source](Data/README_DATA_METHODOLOGY.md), regenerate the page:

```powershell
.venv/Scripts/python.exe Data/scripts/build_documentation.py
```

## Checks and submission

```powershell
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m pip check
npm --prefix frontend run typecheck
npm --prefix frontend test
npm --prefix frontend run build
.venv/Scripts/python.exe -m evaluation.verify_runtime --frontend-url http://127.0.0.1:3000
```

The runtime check requires both servers. To generate the submission archive:

```powershell
.venv/Scripts/python.exe scripts/reproduce_submission.py
```

Additional run instructions: [submission guide](docs/submission_guide.md). Documentation: [data methodology](Data/index.html), [scoring](docs/scoring_methodology.md), [valuation](docs/valuation_methodology.md), [advisor](docs/llm_methodology.md), [responsible AI](docs/responsible_ai.md), and [recorded pipeline verification](evaluation/results/current_pipeline/README.md).
