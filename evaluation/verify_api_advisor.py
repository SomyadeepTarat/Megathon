"""Opt-in live configured API and local fallback checks. Never record credentials.
Run: .venv/bin/python -m evaluation.verify_api_advisor
Uses only explicit synthetic London evaluation fixtures. No memory is installed.
"""
import asyncio
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))


def main():
    from app.core.environment import load_project_environment
    load_project_environment()
    from app.services.llm_service import GroqProvider, OllamaProvider, FallbackProvider, provider_from_env, INTENT_PROMPT, Intent
    provider = provider_from_env()
    primary = provider.primary if isinstance(provider, FallbackProvider) else provider
    if not isinstance(primary, GroqProvider):
        raise ValueError('Configure LLM_PROVIDER=groq to verify the API')
    output = ROOT / 'evaluation/results/api_advisor'
    output.mkdir(parents=True, exist_ok=True)
    calls = []
    originals = {}
    for cls in (GroqProvider, OllamaProvider):
        original = cls.complete
        originals[cls] = original
        async def recorded(self, system, payload, original=original):
            row = {'provider': type(self).__name__, 'model': self.model,
                   'task': 'explanation' if 'answer_facts' in payload else 'intent'}
            start = time.monotonic()
            try:
                value = await original(self, system, payload)
                row['status'] = 'passed'
                return value
            except Exception as exc:
                row.update(status='failed', error_type=type(exc).__name__, http_status=getattr(exc, 'code', None))
                raise
            finally:
                row['seconds'] = round(time.monotonic() - start, 3)
                calls.append(row)
        cls.complete = recorded
    report = {'model': primary.model, 'scope': 'explicit synthetic fixtures; human semantic review remains required', 'memory_implemented': False}
    try:
        # Call primary directly: fallback cannot conceal authentication/model errors.
        intent = asyncio.run(primary.complete(INTENT_PROMPT, {'question': 'Why is my score low?'}))
        assert Intent.model_validate(intent).intent == 'explain'
        report['direct_primary'] = 'passed'
        from evaluation.verify_london_workflow import main as workflow
        workflow(output=output)
        report['workflow'] = 'passed'
        report['workflow_provider_calls'] = list(calls)
        # Failure injection exercises real installed Ollama without breaking API config.
        class FailedPrimary:
            async def complete(self, system, payload):
                raise TimeoutError('Injected test outage')
        backup = OllamaProvider('qwen3:4b', timeout=20)
        result = asyncio.run(FallbackProvider(FailedPrimary(), backup).complete(
            INTENT_PROMPT, {'question': 'Why is my score low?'}))
        assert Intent.model_validate(result).intent == 'explain'
        report['injected_outage_local_fallback'] = 'passed'
        assert any(c['provider'] == 'GroqProvider' and c['task'] == 'explanation' and c['status'] == 'passed' for c in report['workflow_provider_calls'])
        assert not any(c['status'] == 'failed' for c in report['workflow_provider_calls']), 'Primary API failure in workflow; inspect safe call metadata'
        report['status'] = 'passed'
    except Exception as exc:
        report.update(status='failed', error_type=type(exc).__name__, http_status=getattr(exc, 'code', None))
        raise
    finally:
        report['provider_calls'] = calls
        (output / 'provider_verification.json').write_text(json.dumps(report, indent=2) + '\n')
        for cls, original in originals.items():
            cls.complete = original
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
