# Hosted API interpretation verification — 11 October 2026

No customer memory was implemented.

## Configuration

The project-root ignored `.env` supplies the Groq key server-side. The key authenticated at the models endpoint; no credential value was printed or saved in these reports. No Groq-key-like values were found in tracked files. The former `llama-3.3-70b-versatile` selection was absent from the account model list and returned HTTP 404. The available `qwen/qwen3.8-27b` model passed a direct primary-only intent request, so the local configuration, example and default were corrected. The frontend's “Local AI” wording was changed to “AI” because inference may now be hosted.

## Full integrated check

Run `.venv/bin/python -m evaluation.verify_api_advisor`. It executes the synthetic London workflow in a temporary database, preserving the active source data and customer overrides. The harness runs 12 scenarios, 12 budget/objective combinations, five missing-input/support checks and nine advisor questions. Numerical outputs remain owned by the deterministic engines and valuation models. The explanation response schema and grounding validation are unchanged.

The integrated workflow passed, including baseline valuation versus retrofit uplift, missing suitability, budget optimization and a prompt-injection attempt. All numerical-token checks passed. The repeated nine-question workflow produced seven grounded language-model explanations, no generation-validation fallbacks, and two deterministic feasibility/clarification responses. These counts do not certify human factual-quality targets.

The primary API succeeded on direct authentication/model verification and explanation calls, but then returned HTTP 429 during the rapid batch. The configured fallback returned valid JSON from installed local `qwen3:4b`; subsequent calls used its cooldown path. A separately injected primary outage also passed the real local-fallback check. A later direct primary retry succeeded, consistent with a temporary rate limit. The strict API-readiness harness intentionally exited nonzero because a primary call failed; its report is not relabeled as uninterrupted API success. See `provider_verification.json` for provider identities, safe error codes and timings, and `natural_advisor_smoke.json` for answers.

API-only sustained readiness remains unconfirmed. Keep Ollama running for the demo. Higher account limits or fewer closely spaced questions are needed if every demo answer must come from Groq. The quota cannot be increased by repository code.

The final Python suite passed 295 tests plus 34 subtests. Frontend type checking, 26 tests and production build passed. Live backend/frontend servers were started with the corrected API configuration and browser streaming was checked separately.

## Before optional memory

Review the recorded answers for factual and qualitative accuracy, including whether the assistant correctly identifies the weak score components. Automated numeric matching cannot prove that the prose's interpretation is sound. The initial “improve my score” response described consumption intensity as weak despite its high subscore. This was fixed by exposing its relative scale position and rejecting contradictory weak-component wording. A false rejection of a negated guarantee disclaimer was also corrected, with a regression confirming that a later positive guarantee is still blocked. Baseline questions now receive focused valuation evidence, without duplicate ranges. A repeated run attributed the synthetic baseline to current market conditions; a further guard now rejects that wording for illustrative baseline estimates. `final_quality.json` records focused checks after all these fixes. Earlier batch answers remain preserved as diagnostic evidence. Human semantic quality targets remain uncertified.

Session context is feasible later: keep explicit customer preferences, budgets and proposed packages separate from confirmed installed retrofits. Recompute recommendations and numerical estimates from current validated property inputs on every action. Session-only chat history is distinct from the optional extension's persistent customer memory. Neither was added in this task.
