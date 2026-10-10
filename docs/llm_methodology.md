# Person 2: AI advisor implementation and handoff

This implements only the AI engineering portion of the PRD. No frontend or numerical
engine was added. The advisor route is now mounted in the existing application, with
`BackendAdvisorEngines` translating P1's actual assessment/scenario contracts. P4's
production engines and budget optimization still need integration by their owners.

## Audit fixes — 10 October 2026

- Ollama now receives `think: false` and task-specific JSON schemas. Explanation
  selection is restricted to actual supplied fact IDs. Empty or truncated content
  is rejected explicitly. See [Ollama chat API](https://docs.ollama.com/api/chat).
- Negations, comparisons, exclusions and retaining existing systems require an
  explicit full package selection. These are blocked before LLM extraction, even
  if the model proposes a syntactically valid package containing mentioned upgrades.
- Partial assessments/scenarios retain verified figures and explicitly mark missing
  score/carbon/valuation estimates unavailable. A missing optional valuation no longer
  suppresses verified energy evidence.
- Score components, feasible recommendation reasons and valuation intervals are
  rendered as readable sentences instead of raw JSON. Numbers remain server-owned.
- `/advisor/chat` is mounted; no test adapter is installed in production. Actual
  baseline assessments work; absent retrofit/optimizer engines return unavailable.
- `.env.example` includes local `qwen3:4b` settings. No weights are downloaded.

The earlier audit reports a live installed-model run. Ollama is not currently
listening at this checkout's localhost endpoint. Mocked transport/behavior tests do not
establish real-model quality or latency. Rerun live evaluation on the demo machine.

## What the service does

The flow is question → validated intent → server calculation → evidence → explanation.
`backend/app/services/llm_service.py` owns this flow. `backend/app/api/advisor.py`
exposes `POST /advisor/chat`, once included in Person 1's application.

For example, “What if I install only a heat pump?” becomes a `simulate_retrofit`
intent containing `heat_pump`. The service first calls `feasibility`, then `simulate`.
The simulation adapter must recalculate energy, carbon, score and valuation together.
Only after a successful response does the service generate an explanation. A heat
pump's negative electricity savings remain negative; this service performs no arithmetic.

“What if I have only £5,000?” invokes the backend optimizer. The optimizer owns
package search, costs, feasibility, interactions and objective ranking. It must return
the selected package's complete scenario, with confirmed feasibility.

Simple explicit requests use an offline parser. Other questions use Ollama's JSON
intent extraction. Invalid JSON, extra keys, unknown upgrades, negative budgets,
duplicate upgrades, invented budgets/upgrades and provider errors fail validation.
Unclear what-if requests ask for clarification rather than explain an old assessment.
There is no conversation history: “remove it” requires the complete desired package.
The client can resolve ambiguity by sending an explicit `scenario` selection.
For example, “skip insulation and install only a heat pump” asks for confirmation
through a full package selection, rather than letting the LLM decide what was negated.

## Grounding design

The LLM selects evidence IDs instead of writing arbitrary final prose. The service
renders the corresponding backend facts verbatim, with field paths in `facts`.
Unknown IDs or extra response keys trigger deterministic fallback. Missing-data
notices, assumptions, sources and warnings survive relevance selection. The final
response includes the original structured backend result so future frontend components
can render numbers directly from it.

This deliberately conservative, extractive explanation design avoids both invented
numbers and putting a real number against the wrong metric. It is less conversational
than unrestricted LLM text. Backend issue descriptions and recommendation reasons
provide the substantive explanation. Their quality depends on the upstream engines.
Only recommendations explicitly marked `feasible: true` are included in explanation
evidence. Conditional and infeasible scenario packages stop before simulation.
All valuation explanations include the noncausality caveat.

Server-owned evidence is trusted. A compromised or inaccurate numerical engine is
outside this layer's guarantee. Intent extraction still requires real-model evaluation,
especially negation, comparisons and unusual phrasing. The model is never allowed to
choose property IDs, URLs, tools outside the allowlist, or executable code.

## Person 1 integration contract

Run application imports from the repository root. Implement an async adapter with:

```python
async def assessment(property_id: str) -> dict: ...
async def feasibility(property_id: str, retrofits: list[str]) -> dict: ...
async def simulate(property_id: str, retrofits: list[str],
                   budget_gbp: float | int | None, objective: str) -> dict: ...
async def optimize(property_id: str, budget_gbp: float | int, objective: str) -> dict: ...
```

Wrap synchronous CPU work appropriately in Person 1's adapter. Raise `PropertyNotFound`
for absent properties and `EngineUnavailable` for expected missing data/dependencies.
Other programming errors are intentionally not swallowed. Apply the application's
authentication and property-access checks before loading a customer's property.

Completed assessment/simulation/optimization output must have `property_id` matching
the request and `status: "success"` or `"partial"`. Simulation/optimization must also include
`feasibility: {"all_feasible": true, "rejected_retrofits": []}`. Unknown eligibility
must not be marked true. Feasibility checks can supply `conditional_retrofits`.
The selected package should be included in optimization output for frontend display.
Use the PRD section 14.3 nested `score`, `energy`, `carbon`, `valuation`, `assumptions`
and `warnings` structure. Optional `issues`, `sources`, `recommendations` and
`score.components` supply explanation evidence. For an assessment, put the current
score under `score.baseline`; do not provide a fictional after score.
The adapter may translate other upstream shapes into this contract.

Numbers must be finite; use null and explicit section status for unavailable estimates.
Sections with status `unavailable`, `awaiting_factors`, or `missing_data` get an
unavailable notice. Include provenance in `sources`/`assumptions`, including synthetic
or imputed inputs. Do not put customer addresses or secrets in explanation evidence.

The existing `app.main` already registers the router and real adapter at startup.
For a different application, the registration pattern is (do not register it twice):

```python
from backend.app.api.advisor import router
from backend.app.services.llm_service import AdvisorService, provider_from_env

app.include_router(router)
app.state.advisor_service = AdvisorService(
    engines=your_engine_adapter,
    provider=provider_from_env(),
)
```

An unconfigured standalone router returns HTTP 503. The production app configures it
with real backend adapters. Missing properties return HTTP 404; invalid
request schemas return HTTP 422. Domain outcomes use `ChatResponse.status`:
`success`, `partial`, `clarification_required`, `unavailable`, `infeasible`, `conditional`.
`tool_calls` records operations attempted, not proof those operations succeeded.

Example request:

```json
{
  "property_id": "P10001",
  "message": "What if I skip insulation and install only a heat pump?",
  "scenario": {
    "intent": "simulate_retrofit",
    "retrofits": ["heat_pump"],
    "budget_gbp": null,
    "objective": "carbon_reduction"
  }
}
```

Omit `scenario` to use natural-language extraction. An explicit empty `retrofits` list
requests a baseline package; an omitted package is never silently treated as empty.
Allowed objectives are `carbon_reduction`, `energy_reduction`, `shortest_payback`.
Only enable objectives actually supported by the numerical engine.

## Local Ollama setup (PowerShell)

Install Ollama separately if needed and start its local server. Choose an installed
model after checking `ollama list`. This implementation does not download model weights.

```powershell
python -m pip install -r backend/requirements-advisor.txt
ollama list
$env:LLM_PROVIDER = 'ollama'
$env:LLM_MODEL = 'YOUR_INSTALLED_MODEL_NAME'
$env:OLLAMA_BASE_URL = 'http://127.0.0.1:11434'
$env:LLM_TIMEOUT_SECONDS = '20'
```

Then start the integrated backend using Person 1's command. `.env.example` documents
the settings; the service reads environment variables, not `.env` files automatically.
For fully offline explanations without model inference set `LLM_PROVIDER=deterministic`.
Local Ollama needs no API key. Hosted providers can implement the small `Provider`
protocol later; none are enabled here.

The Ollama adapter uses `/api/chat`, JSON format, nonstreaming responses, bounded
response size and request timeout. Reference: [official Ollama API documentation](https://github.com/ollama/ollama/blob/main/docs/api.md).
There is no automatic retry; failure falls back promptly. An ambiguous question may
need both intent and explanation calls, so total model time can approach twice the
configured per-call timeout. Cold model loads may time out; fallback remains usable.

## Verification and remaining evaluation

```powershell
python -m pytest backend/tests/test_llm_service.py backend/tests/test_advisor_regressions.py -q
```

The offline suite uses synthetic test evidence and a fake provider. The regression
suite also exercises the mounted production app without dependency overrides. It checks routing,
negative savings, feasibility gates, budgets, missing results, property identity,
schema validation, malformed provider output, provenance and fallback. The Ollama
transport test mocks the HTTP response; it does not test a real model.

The existing Person 5 `evaluation/explanation_cases.json` has 25 human-review cases.
Run the live transport/service regression on a machine running Ollama using actual
configured backend dependencies:

```powershell
python backend/probe_advisor.py --model qwen3:4b
```

This writes `docs/advisor_live_results.json` with outcomes, modes, timings and provider
error types; it exits unsuccessfully if any model call fails or no explanation reaches
`grounded_llm` mode. It never replaces missing scenario engines with fixtures. This
report is a diagnostic record, not a human-reviewed input to P5's quality evaluator.

After engine integration and local Ollama startup, record actual responses for those
questions, derive `allowed_numbers` from the backend evidence, and have a reviewer
fill the existing review fields. Then run:

```powershell
python -m evaluation.evaluate_explanations --input PATH_TO_RECORDED_RESPONSES.json
```

Do not fill reviewer labels automatically. Passing service tests does not establish
groundedness ≥90%, factual accuracy ≥90%, or unsupported claims <5%. Live model
quality and complete system integration remain unverified until that run is performed.
