"""Opt-in live Ollama regression run using real configured backend dependencies.

Run from the repository root: python backend/probe_advisor.py --model qwen3:4b
No weights are downloaded and no human quality scores are inferred.
"""
import argparse
import asyncio
from collections import Counter
import json
from pathlib import Path
import time


async def run(args):
    from app.main import app, get_repository
    from app.services.llm_service import AdvisorService, ChatRequest, OllamaProvider

    class RecordingProvider:
        def __init__(self):
            self.provider = OllamaProvider(args.model, args.base_url, args.timeout)
            self.calls = []

        async def complete(self, system, payload):
            start = time.monotonic()
            item = {'task': 'explanation' if 'facts' in payload else 'intent'}
            self.calls.append(item)
            try:
                value = await self.provider.complete(system, payload)
                item['status'] = 'returned_json'
                return value
            except Exception as exc:
                item.update(status='failed', error_type=type(exc).__name__)
                raise
            finally:
                item['seconds'] = time.monotonic() - start

    provider = RecordingProvider()
    service = AdvisorService(app.state.advisor_service.engines, provider)
    property_id = args.property_id or get_repository().list_properties()[0].property.property_id
    rows = []
    for case in json.loads(args.cases.read_text(encoding='utf-8')):
        start = time.monotonic()
        response = await service.chat(ChatRequest(property_id=property_id, message=case['question']))
        rows.append({'case_id': case['case_id'], 'question': case['question'],
                     'seconds': time.monotonic() - start, 'response': response.model_dump(mode='json')})
        print(case['case_id'], response.status, response.mode, flush=True)
    report = {'model': args.model, 'property_id': property_id, 'records': rows,
              'modes': dict(Counter(row['response']['mode'] for row in rows)),
              'statuses': dict(Counter(row['response']['status'] for row in rows)),
              'provider_calls': provider.calls, 'human_reviewed': 0,
              'limitations': 'Real baseline engine and current production dependencies. Missing scenario/optimizer engines stay unavailable. No human quality targets certified.'}
    args.output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('Saved:', args.output)
    return 1 if any(call['status'] == 'failed' for call in provider.calls) or not report['modes'].get('grounded_llm') else 0


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', required=True, help='An already installed local model')
    parser.add_argument('--base-url', default='http://127.0.0.1:11434')
    parser.add_argument('--timeout', type=float, default=20)
    parser.add_argument('--property-id')
    parser.add_argument('--cases', type=Path, default=root / 'evaluation/explanation_cases.json')
    parser.add_argument('--output', type=Path, default=root / 'docs/advisor_live_results.json')
    args = parser.parse_args()
    if not 0 < args.timeout <= 60:
        parser.error('--timeout must be in (0, 60]')
    raise SystemExit(asyncio.run(run(args)))
