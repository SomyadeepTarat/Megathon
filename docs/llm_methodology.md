# Grounded natural-language advisor

The official Lloyds problem statement (LLOYDS-ps2.pdf), sections 1, 8 and 11,
requires the LLM to explain documented calculations and answer what-if questions
only after the relevant models rerun. Explanations are evaluated for groundedness,
factual accuracy, completeness and correct missing-data/infeasibility handling.
Customer memory is optional; the current browser sends no follow-up context.

## Runtime flow

The service interprets the current question, validates a structured intent, calls
assessment/recommendation/feasibility/simulation/optimization tools as required,
and gives the language model a bounded set of relevant verified facts plus
explicit domain definitions. Scores, estimates and model outputs are never
calculated by the LLM. Infeasible upgrades stop before simulation and explain
the exact backend blocker. Missing budgets ask for an amount rather than showing
an unrelated package selector. Missing estimates retain their reasons.

The LLM now writes conversational prose addressing the question instead of merely
selecting facts to copy. Each sentence cites internal fact IDs. These IDs are not
shown in the answer. Numerical values are masked in the language-model context;
the model selects metric fact IDs and the server writes numerical sentences with
known units, signs and baseline/after attribution. Displayed numerical sentences
use at most two decimal places, while full original evidence remains available.
A final score must not be described as a gain. Property-value effects are rendered
as ranges, not guaranteed single premiums. Independent upgrade simulations are
never added as a package. Full limitations remain in an expandable evidence panel.
Synthetic-data estimates are identified in the visible answer.

Validation rejects malformed schemas, unknown evidence IDs, generated digits,
invalid placeholders, spelled-out quantitative estimates, guarantees, and the
known error of describing a heat pump as reducing required thermal demand. A
failed or unavailable provider uses conversational deterministic explanations.
This is a mechanical grounding guard, not a proof that every qualitative sentence
is true. Citations can still be misinterpreted. Human review is required to claim
the official targets: groundedness >=90%, factual accuracy >=90%, unsupported
claims <5%.

## Local demo configuration

```
LLM_PROVIDER=ollama
LLM_MODEL=qwen3:4b
OLLAMA_BASE_URL=http://127.0.0.1:11434
LLM_TIMEOUT_SECONDS=20
```

The Ollama provider uses a task-specific JSON schema, temperature zero, thinking
disabled, an 8192-token context, up to 640 answer tokens, and a 15-minute model
keep-alive. Common explicit requests bypass model intent extraction. Keep Ollama
running once; restart the backend after edits and rebuild/restart the frontend
after frontend changes. Optional warm-up: `ollama run qwen3:4b "Reply with OK"`.

`POST /advisor/chat` retains JSON responses. `/advisor/chat/stream` emits actual
tool-boundary progress and then one validated answer. Unvalidated model tokens
are not streamed. The application does not imply a live meter feed.

## Evaluation and practical limits

`evaluation/results/current_pipeline/natural_advisor_smoke.json` records actual
engine-backed local answers and timing. `natural_advisor_review.json` is a new
human-review sheet; review labels must be filled by a person, not generated.
`natural_advisor_metrics.json` reports numeric checking and explicitly leaves
semantic targets unverified until human review. The earlier fact-selection
and historical advisor reports do not establish quality of this prose generator.

During development the small local model incorrectly relabelled a final score
as an increase and claimed a heat pump reduced heating demand. Both cases led
to safeguards. The final eight-case sample included six LLM-generated answers, one generation-validation fallback and one direct infeasibility response. Generated answers took approximately 1.8–4.8 seconds, and numeric token checking found no unsupported figures. Local answers generally took several seconds; invalid generations
remain possible and are replaced by natural fallbacks. Local Ollama is usable
for a guarded offline demo, but this small sample is not an SLA or official quality
certification. If consistently stronger interpretation is required, evaluate a
stronger hosted model that supports strict structured output with the same guards.
A provider upgrade requires a fresh scenario and human evaluation; it does not
justify relaxing numerical or feasibility constraints. No cloud provider, API
key, purchase or external-data transfer was configured by this change.

Reproduce the smoke run with:

```bash
LLM_PROVIDER=ollama LLM_MODEL=qwen3:4b OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 .venv/bin/python -m evaluation.verify_natural_advisor
```
