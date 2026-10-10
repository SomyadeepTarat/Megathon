"""Reproducible local advisor smoke test; does not replace human semantic review.

Run: LLM_PROVIDER=ollama LLM_MODEL=qwen3:4b python -m evaluation.verify_natural_advisor
"""
import json
import os
import sys
import tempfile
import time
from decimal import Decimal
from pathlib import Path
from evaluation.evaluate_explanations import NUMBER, REVIEW_FIELDS, evaluate

CASES = [
    ('DEMO-P00005', 'Why is my score low?'),
    ('DEMO-P00005', 'How do I improve my score?'),
    ('DEMO-P00001', 'What if I install a heat pump?'),
    ('DEMO-P00005', 'What is a heat pump and could it help my home?'),
    ('DEMO-P00005', 'How much could my property value change?'),
    ('DEMO-P00003', 'What if I install a heat pump?'),
    ('DEMO-P00001', 'What can I do with a £5000 budget?'),
    ('DEMO-P00005', 'How is carbon reduction calculated?'),
]


def write_evaluation(data, output):
    rows = []
    for index, case in enumerate(data['cases']):
        answer = case['answer']; allowed = set()
        for fact in answer.get('facts', []):
            for token in NUMBER.findall(fact['text']):
                value = Decimal(token.replace(',', ''))
                allowed.update((str(value), str(value.quantize(Decimal('.01')))))
        rows.append({'case_id': f'natural-{index + 1:02}', 'question': case['question'],
                     'property_id': case['property_id'], 'response': answer['explanation'],
                     'allowed_numbers': sorted(allowed), 'mode': answer['mode'],
                     'reviewer': 'somyadeep', 'review': {key: None for key in REVIEW_FIELDS}, 'notes': ''})
    metrics = evaluate(rows)
    metrics.update(local_latency_seconds=[case['seconds'] for case in data['cases']],
                   grounded_llm_responses=sum(c['answer']['mode'] == 'grounded_llm' for c in data['cases']),
                   generation_validation_fallbacks=sum(bool(c['answer']['fallback_reason']) for c in data['cases']))
    output.mkdir(parents=True, exist_ok=True)
    (output / 'natural_advisor_smoke.json').write_text(json.dumps(data, indent=2))
    (output / 'natural_advisor_metrics.json').write_text(json.dumps(metrics, indent=2))
    review_path = output / 'natural_advisor_review.json'
    if review_path.exists():
        previous = json.loads(review_path.read_text())
        if any(any(type(value) is bool for value in r.get('review', {}).values()) for r in previous):
            review_path = output / 'natural_advisor_review_latest.json'
    review_path.write_text(json.dumps(rows, indent=2))
    return metrics


def main():
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / 'backend'))
    os.environ.setdefault('OMP_NUM_THREADS', '1')
    os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
    with tempfile.TemporaryDirectory(prefix='natural-advisor-') as temporary:
        os.environ['GREENPRINT_DB_PATH'] = str(Path(temporary) / 'properties.db')
        os.environ['GREENPRINT_PROPERTY_DATASET'] = 'demo'
        from app.main import app
        from fastapi.testclient import TestClient
        records = []
        with TestClient(app) as client:
            for property_id, question in CASES:
                start = time.perf_counter()
                response = client.post('/advisor/chat', json={'property_id': property_id, 'message': question})
                response.raise_for_status()
                answer = response.json()
                assert answer['explanation'].strip()
                if property_id == 'DEMO-P00003':
                    assert answer['status'] == 'infeasible' and 'simulate' not in answer['tool_calls']
                records.append(dict(question=question, property_id=property_id,
                                    seconds=round(time.perf_counter() - start, 3), answer=answer))
                print(f"{answer['mode']}: {question}", flush=True)
        metrics = write_evaluation({'scope': 'Eight local engine-backed smoke cases; semantic targets require human review',
                                    'provider': os.getenv('LLM_PROVIDER', 'deterministic'), 'cases': records},
                                   root / 'evaluation/results/current_pipeline')
        print(json.dumps(metrics, indent=2))
        if metrics['responses_with_unsupported_numbers_fraction']:
            raise SystemExit('Unsupported numerical tokens were found')


if __name__ == '__main__':
    main()
