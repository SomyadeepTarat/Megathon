"""Run consistency checks on recorded P1/P4 outputs without importing their code."""
import argparse
import json
from pathlib import Path
from evaluation.checks import check_energy, check_score


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, required=True, help="JSON array of cases: case_id, energy and/or score, optional factors")
    a = p.parse_args()
    rows = json.loads(a.input.read_text())
    if not rows:
        raise ValueError("No scenarios recorded")
    results = []
    for row in rows:
        try:
            if "energy" not in row and "score" not in row:
                raise AssertionError("No checkable outputs")
            if "energy" in row:
                check_energy(row["energy"], row.get("factors"))
            if "score" in row:
                check_score(row["score"])
            results.append({"case_id": row["case_id"], "passed": True})
        except (AssertionError, KeyError, TypeError, ValueError) as error:
            results.append({"case_id": row["case_id"], "passed": False, "reason": str(error)})
    print(json.dumps({"kind": "implementation_verification", "results": results}, indent=2))
    if not all(r["passed"] for r in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
