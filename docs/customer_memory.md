# Persistent customer memory

Kew remembers explicit preferences and responses so customers do not need to repeat their constraints. Memory changes the candidate packages considered; scores, energy, carbon, bills, payback and valuation still come from the existing engines using current assessment inputs. Synthetic estimates remain synthetic.

## Using it

1. Open Kew on the selected home and expand **What Kew remembers**.
2. Set a maximum budget, priority and any unwanted upgrades; press **Save memory**.
3. Press **Use my saved preferences** to calculate recommendations under those constraints.
4. Respond to a recent package with **Interested**, **Not for me**, or **Later**. The latter two exclude that exact combination from subsequent searches. Interested restores eligibility; it does not install anything.
5. Confirm completed work separately. Update Assessment to reflect installed features and current energy/physical inputs. If the recorded baseline still contradicts completed work, further improvement estimates are blocked with an explanation.
6. Reload the browser or restart the server: saved choices remain. Reset clears customer preferences and this home's history, feedback, completed-work record and follow-up context. Another home's completed-work record is retained.

A supported explicit chat command is `Remember my budget is £2,750`. It saves locally without an LLM call. General free-text preferences are not silently extracted or inferred: use the controls to confirm them.

## Storage and consistency

The `customer_memory` table shares the editable-property SQLite database (`GREENPRINT_DB_PATH`; by default `backend/data/london_user_properties.db`). Back up this file to preserve memory. Deleting it resets local persistence.

Canonical source `customer_id` identifies shared customer preferences; editable provenance cannot transfer that identity. Homes without a canonical customer ID receive property-scoped memory. Completed work, feedback, the last validated action and at most 20 recent action records are scoped to each home. Full chat transcripts and old numerical estimates are not retained. Follow-ups can reuse a stored action after restart, but recompute it against current inputs.

Writes are atomic transactions with revision checks. A stale settings save returns HTTP 409 and the UI reloads the latest version. If preferences change while a chat calculation is running, its answer discloses that it used the earlier revision and asks for recalculation.

Advisor and planner simulation, recommendation and optimization endpoints enforce the same exclusions and completed-work guard. Explicit planner budgets and objectives take precedence over saved defaults; an omitted budget can use the remembered maximum. Property portfolio rankings retain their general analytical purpose. Stored historical recommendation snapshots are not retroactively rewritten: recalculate after changing memory.

Memory does not fill missing measurements, manufacture a new EPC, imply observed savings, or turn an accepted recommendation into completed work. Completed flags are checked for consistency, but this does not prove that energy readings are post-installation: customers must update their actual baseline inputs.

This local demo has no authenticated account system. Canonical identity provides consistent routing, not access control. A public multi-user deployment requires authenticated ownership checks on property and memory endpoints, plus retention/privacy controls.

## Verification and API usage

Run the offline verification (zero provider calls):

```sh
.venv/bin/python -m evaluation.verify_customer_memory
.venv/bin/python -m pytest backend/tests/test_customer_memory.py -q
```

The curated synthetic fixture uses a £1,733 budget and energy-reduction priority. Initially it selects loft insulation plus a smart thermostat (£1,700). Rejecting that combination and reopening the database changes the selection to loft insulation (£1,500). These are fixture results, not real-world measured performance.

A single live Groq check passed using `qwen/qwen3.8-27b`; the answer was accepted by existing grounding checks. Evidence is in `evaluation/results/customer_memory/live.json`. The optional command below permits exactly one explanation call, no live intent extraction, retries or fallback calls, with a 60-second repeat-check guard:

```sh
.venv/bin/python -m evaluation.verify_customer_memory --live-api
```

Tests cover persistence, customer/home isolation, stale revisions, zero/invalid budgets, feedback-driven package changes, explicit overrides, follow-up recalculation, completed-baseline consistency, missing homes, planner/advisor consistency and provider call count. An automated grounding pass is not a substitute for human explanation review.
