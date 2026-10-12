# Kew — Setup and Run

## Requirements

Use Python 3.14.7 and Node.js 26.8.2. Run application commands from `project/`.

## Install

```bash
git clone https://github.com/SomyadeepTarat/Megathon.git
cd Megathon/project
mkdir -p ../deliverables
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
npm --prefix frontend ci
```

## Data and model preparation

Dataset files are available in [Data/csv](https://github.com/SomyadeepTarat/Megathon/tree/main/project/Data/csv) and [backend/data](https://github.com/SomyadeepTarat/Megathon/tree/main/project/backend/data). Clone the repository to obtain them; they are excluded from the submission code ZIP. No external model-weight download is required: generate model artifacts with the commands below.

```bash
.venv/bin/python -m ml.train_valuation --data Data/csv/properties.csv --provenance ml/snapshot_provenance.json --target-kind snapshot --seed 42 --output ml/models/snapshot.joblib --reports ml/reports/snapshot
.venv/bin/python -m ml.synthetic_impact
.venv/bin/python scripts/prepare_demo.py
```

For the London dataset, also run:

```bash
.venv/bin/python scripts/prepare_london_demo.py
```

## Backend

For local development, start both the backend and frontend together from `project/`:

```bash
bash scripts/dev.sh
```

Open [Kew](http://127.0.0.1:3000), select a property, and use Assessment or Retrofit planner. The script waits for the backend before starting the frontend; Ctrl+C stops the services it started. Run the data and model preparation above first.

Start the prepared demo dataset:

```bash
GREENPRINT_PROPERTY_DATASET=demo LLM_PROVIDER=deterministic .venv/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8001
```

Use `GREENPRINT_PROPERTY_DATASET=london` after London preparation. Open [API documentation](http://127.0.0.1:8001/docs) or [health check](http://127.0.0.1:8001/health).

## Frontend

In another terminal, build and start:

```bash
GREENPRINT_BACKEND_URL=http://127.0.0.1:8001 npm --prefix frontend run build
GREENPRINT_BACKEND_URL=http://127.0.0.1:8001 npm --prefix frontend start -- --port 3000
```

Open [the app](http://127.0.0.1:3000). For development, use `npm --prefix frontend run dev -- --port 3000` instead.

## Optional AI configuration

The backend loads the `project/.env`; shell variables take precedence. Create `.env` inside `project/` locally with these values to enable Groq:

```dotenv
LLM_PROVIDER=groq
GROQ_API_KEY=replace_with_your_key
GROQ_MODEL=llama-3.3-70b-versatile
LLM_FALLBACK_PROVIDER=deterministic
```

To use installed local Ollama as backup, set `LLM_FALLBACK_PROVIDER=ollama`, `OLLAMA_MODEL=qwen3:4b` and `OLLAMA_BASE_URL=http://127.0.0.1:11434`. Keep keys out of Git and frontend configuration. Use `LLM_PROVIDER=deterministic` to run without an AI service.

## Render run commands

Backend Render root directory: `project`. Build with the installation and model-preparation commands above; start with:

```bash
python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT
```

Set `GREENPRINT_PROPERTY_DATASET=demo` unless the London preparation command is included in the build. Frontend Render root directory: `project/frontend`. Build with `npm ci && npm run build`; start with `npm start -- --port $PORT`. Set `GREENPRINT_BACKEND_URL` to the backend's HTTPS URL before building.

For persistent storage, set `GREENPRINT_DB_PATH` to a writable persistent-disk path. Local SQLite files on Render Free are temporary.

## Verify and package

```bash
.venv/bin/python -m pytest -q
npm --prefix frontend run typecheck
npm --prefix frontend test
.venv/bin/python scripts/reproduce_submission.py
.venv/bin/python scripts/build_code_zip.py
```

Submit `project/submission/megathon-code.zip` as the code backup. The separate `greenprint-team-254.zip` is a local reproduction bundle containing data and models; it is not the code ZIP required by the submission rules.
