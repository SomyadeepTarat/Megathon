# Backend integration verification

Verified on Python 3.14: 62 tests passed across backend/tests, ml/tests and evaluation/tests. Backend accounts for 43 tests. Existing teammate ML and evaluation tests passed without modifying their source files. Exact installed versions are in the repository-root requirements.lock.txt. Backend-only versions are in backend/requirements.lock.txt.

Command from repository root:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python -m pytest -q
```

The suite emits one upstream Starlette TestClient/httpx deprecation warning. It does not affect the passing test results. Other Python versions were not verified during this run.

Live HTTP checks on port 8002 confirmed GET /health, GET /properties, GET /properties/DEMO1/assessment, and GET /openapi.json return 200. POST /scenarios/simulate returns 503 with typed unavailable feasibility and no scenario energy estimates while P4 is absent.

Integration tests verify signed heat-pump fuel changes, updated heating score, unchanged recorded EPC, baseline isolation, missing consumption, zero baseline handling, conditional/infeasible rejection, budget rejection, exact measure coverage, output consistency, carbon arithmetic, dependency injection, property route behavior, and valuation field translation.

Fixture engines and carbon factors exist only in tests. These checks establish software correctness and integration behavior, not real-world energy or property-value accuracy. Runtime property records are labeled synthetic development examples and have no invented benchmark.

No original teammate files under ml/, evaluation/, or backend/app/services/valuation_service.py were edited. Backend-owned Python files were checked for absence of comments and docstrings.
