"""Numbers are checked against explicit allowed claims; semantics need human review."""
import argparse
import json
import re
from decimal import Decimal
from pathlib import Path

NUMBER = re.compile(r"(?<![\w.])[-+]?\d+(?:,\d{3})*(?:\.\d+)?")
REVIEW_FIELDS = ["groundedness", "factual_accuracy", "completeness", "tool_invocation", "unavailable_handling", "no_unsupported_claims"]


def evaluate(rows):
    if not rows:
        raise ValueError("No recorded responses supplied")
    checks = []
    for row in rows:
        if not isinstance(row.get("response"), str) or not row["response"].strip():
            raise ValueError(f"Record an actual response for {row.get('case_id')}")
        # Whitelist must be created from structured outputs, with displayed rounding.
        allowed = {Decimal(str(v).replace(",", "")) for v in row.get("allowed_numbers", [])}
        numbers = [Decimal(m.group().replace(",", "")) for m in NUMBER.finditer(row["response"])]
        unsupported = [str(v) for v in numbers if v not in allowed]
        checks.append({"case_id": row["case_id"], "unsupported_numeric_tokens": unsupported,
                       "numeric_tokens": len(numbers)})
    reviewed = [r for r in rows if r.get("reviewer") and all(type(r.get("review", {}).get(k)) is bool for k in REVIEW_FIELDS)]
    human = {k: sum(r["review"][k] for r in reviewed) / len(reviewed) for k in REVIEW_FIELDS} if reviewed else None
    return {"responses": len(rows), "human_reviewed": len(reviewed), "human_metrics": human,
            "responses_with_unsupported_numbers_fraction": sum(bool(c["unsupported_numeric_tokens"]) for c in checks) / len(rows),
            "checks": checks, "targets_met": None if len(reviewed) != len(rows) else
            human["groundedness"] >= .9 and human["factual_accuracy"] >= .9 and
            1 - human["no_unsupported_claims"] < .05 and
            sum(bool(c["unsupported_numeric_tokens"]) for c in checks) / len(rows) < .05,
            "limitations": "Token matching cannot verify units, attribution, semantics or unsupported nonnumeric claims. Human review required."}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(evaluate(json.loads(a.input.read_text())), indent=2))
