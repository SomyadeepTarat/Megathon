"""Compare installed model JSON transport with default and disabled thinking.

Diagnostic only: does not modify Person 2's production provider.
"""
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.llm_service import INTENT_PROMPT, EXPLANATION_PROMPT, Intent


def main():
    rows = []
    cases = [
        ("intent_default", None, INTENT_PROMPT, {"question": "What if I install a heat pump but not solar panels?"}),
        ("intent_no_thinking", False, INTENT_PROMPT, {"question": "What if I install a heat pump but not solar panels?"}),
        ("explanation_no_thinking", False, EXPLANATION_PROMPT,
         {"question": "Why is the score unavailable?", "facts": [
             {"id": "f0", "source": "score.status", "text": "Score estimate is unavailable."},
             {"id": "f1", "source": "warnings.0", "text": "A documented consumption benchmark is missing."}]}),
    ]
    for name, think, system, payload in cases:
        body = {"model": "qwen3:4b", "stream": False, "format": "json",
                "options": {"temperature": 0, "num_predict": 512},
                "messages": [{"role": "system", "content": system},
                             {"role": "user", "content": json.dumps(payload)}]}
        if think is not None:
            body["think"] = think
        start = time.perf_counter()
        request = urllib.request.Request("http://127.0.0.1:11434/api/chat", json.dumps(body).encode(),
                                         {"Content-Type": "application/json"})
        row = {"case": name, "think": think}
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = json.load(response)
            row.update(content=raw.get("message", {}).get("content"),
                       thinking_characters=len(raw.get("message", {}).get("thinking", "")),
                       done_reason=raw.get("done_reason"), eval_count=raw.get("eval_count"))
            try:
                result = json.loads(row["content"])
                row["parsed_json"] = result
                if name.startswith("intent"):
                    row["validated_intent"] = Intent.model_validate(result).model_dump()
                else:
                    row["valid_fact_selection"] = (set(result) == {"fact_ids"} and
                                                   bool(result["fact_ids"]) and
                                                   all(x in {"f0", "f1"} for x in result["fact_ids"]))
            except (ValueError, TypeError) as error:
                row["validation_error"] = type(error).__name__
        except Exception as error:
            row["transport_error"] = type(error).__name__
        row["seconds"] = time.perf_counter()-start
        rows.append(row)
        print(json.dumps(row), flush=True)
    path = ROOT / "evaluation/results/full_pipeline/ollama_transport_probe.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
