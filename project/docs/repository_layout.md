# Repository layout

The repository root contains project/, LICENSE, README.md and an empty deliverables/ directory. Application commands run inside project/. Existing milestone PDFs are preserved in project/deliverables_archive/. Git cannot track an empty directory; setup creates deliverables/ and the code ZIP includes it explicitly. Render backend root directory is project; frontend root directory is project/frontend.

| Directory | Purpose |
|---|---|
| frontend/ | Next.js pages, components, UI tests and assets |
| backend/ | FastAPI routes, database migrations, service adapters and backend tests |
| carbon_engine/ | Shared retrofit and per-fuel carbon calculations |
| ml/ | Model training, inference and evaluation |
| Data/ | Data generation scripts, reference documentation and datasets |
| evaluation/ | Cross-component verification and evaluation evidence |
| scripts/ | Setup, reproduction and packaging commands |
| docs/ | Architecture, methodology and project explanation |
| deliverables_archive/ | Preserved earlier milestone PDFs |
| submission/ | Ignored locally generated ZIPs |

The root README contains setup/run instructions only. The earlier explanation is preserved in project_overview.md. Shared Python modules remain at their current paths because backend imports, training scripts and Render commands depend on them. Dependencies, caches, local SQLite databases, .env secrets and generated bundles are ignored by Git.

## Official deliverables

- Earlier milestone files are preserved in project/deliverables_archive/; root deliverables/ is empty as requested.
- The submission rules call for a final report of at most three pages; add official PDFs to root deliverables/ when preparing the final submission.
- Every PDF needs the team number at the top. PDFs and videos must not contain team names, member names or college names.
- Submit a screen-recorded voiceover demo, maximum four minutes, through the official form using a Google Drive link accessible to anyone with the link.
- Create the code-only ZIP with scripts/build_code_zip.py; it excludes datasets, model weights and dependencies. The reproduction bundle is a separate artifact and is not the official code ZIP.
- Only main is evaluated. User must commit and push the reviewed files by the official deadline.
- Submit slides as PDF through the slides form; do not put slides in the archived repository after the final deadline.

The supplied MIT license copyright is retained exactly in LICENSE. Existing third-party notices, including the Three.js license, are retained and continue to apply to their respective code.
