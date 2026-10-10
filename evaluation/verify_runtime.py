"""Exercise production routes across supplied homes and curated demo scenarios.

Run: python -m evaluation.verify_runtime [--frontend-url http://127.0.0.1:3000]
No dependency overrides or test numerical engines are installed.
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from fastapi.testclient import TestClient
from app.main import app
from app import main as runtime
from app.db.repository import CsvPropertyRepository, JsonPropertyRepository, EditableRepository


def run(frontend_url=None):
    results = {'supplied_dataset': {}, 'curated_demo': [], 'live_frontend': []}
    previous = runtime.repository
    try:
        runtime.repository = EditableRepository(CsvPropertyRepository.from_project_root(ROOT))
        with TestClient(app) as client:
            statuses = Counter()
            for summary in client.get('/properties').json():
                identifier = summary['property_id']
                row = client.get(f'/properties/{identifier}').json()
                payload = {k: v for k, v in row.items() if k not in ('dataset_kind', 'dataset_source')}
                response = client.post('/assessments/full', json=payload)
                assert response.status_code == 200, response.text
                full = response.json()
                assert full['assessment']['score']['status'] == 'available'
                assert full['baseline_carbon']['status'] == 'available'
                valuation = client.get(f'/properties/{identifier}/valuation')
                assert valuation.status_code == 200
                statuses[valuation.json()['status']] += 1
            assert len(client.get('/portfolio/rank').json()) == 100
            results['supplied_dataset'] = {'properties': 100, 'complete_scores': 100,
                'baseline_carbon_available': 100, 'baseline_valuation_statuses': dict(statuses)}

        runtime.repository = EditableRepository(JsonPropertyRepository(ROOT / 'backend/data/curated_demo_properties.json'))
        with TestClient(app) as client:
            for row in runtime.repository.list_properties():
                payload = row.model_dump(mode='json', exclude={'dataset_kind', 'dataset_source'})
                sample = {'property_id': row.property.property_id, 'objectives': {}}
                for objective in ('carbon_reduction', 'energy_reduction', 'shortest_payback'):
                    response = client.post('/retrofits/optimize', json={**payload, 'budget_gbp': 15000, 'objective': objective})
                    assert response.status_code == 200, response.text
                    value = response.json()
                    assert len(value['package_decisions']) == 32
                    best = value['best_scenario']
                    if best:
                        assert best['installation_cost_gbp'] <= 15000
                        assert all(x['status'] == 'feasible' for x in best['feasibility']['items'])
                        assert best['energy']['after']['electricity_kwh'] >= 0
                        assert best['energy']['after']['gas_kwh'] >= 0
                        assert best['valuation']['status'] == 'unavailable'
                    sample['objectives'][objective] = {'status': value['status'],
                        'package': best['applied_retrofits'] if best else None,
                        'reason': value['reason'], 'decisions': value['package_decisions']}
                recommendation = client.post('/retrofits/recommend', json={**payload, 'budget_gbp': 15000})
                assert recommendation.status_code == 200, recommendation.text
                results['curated_demo'].append(sample)
            portfolio = client.get('/portfolio/rank')
            assert portfolio.status_code == 200 and len(portfolio.json()) == 10
            results['curated_portfolio'] = portfolio.json()
            row = runtime.repository.list_properties()[0]
            for package, tools in [(['heat_pump'], ['feasibility', 'simulate']),
                                   (['solar_panels'], ['feasibility', 'simulate']),
                                   (['loft_insulation', 'double_glazing'], ['feasibility', 'simulate'])]:
                response = client.post('/advisor/chat', json={'property_id': row.property.property_id,
                    'message': 'Explain this selected package', 'scenario': {'intent': 'simulate_retrofit',
                    'retrofits': package, 'budget_gbp': 15000, 'objective': 'carbon_reduction'}})
                assert response.status_code == 200, response.text
                assert response.json()['tool_calls'] == tools, response.text
                assert response.json()['status'] in ('success', 'partial'), response.text
            incomplete = row.property.model_dump(mode='json')
            incomplete.update(floor_area_m2=None, region=None, property_type=None)
            unavailable = client.post(f'/properties/{row.property.property_id}/valuation/impact',
                                      json={'scenario_property': incomplete})
            assert unavailable.status_code == 200, unavailable.text
            value = unavailable.json()
            assert value['status'] == 'unavailable'
            assert all(value[field] is None for field in ('value_before', 'value_after', 'uplift_range'))
            results['missing_critical_fields'] = value
    finally:
        runtime.repository = previous
    if frontend_url:
        import httpx
        with httpx.Client(base_url=frontend_url, timeout=30) as client:
            for path in ('/', '/assessment', '/planner', '/compare', '/portfolio', '/api/backend/health', '/api/backend/properties'):
                response = client.get(path)
                assert response.status_code == 200, f'{path}: {response.status_code}'
                results['live_frontend'].append({'path': path, 'status': response.status_code})
    results['status'] = 'passed'
    results['limitations'] = ['Synthetic data and demo assumptions; no observed-market accuracy claim.',
        'HTTP checks do not replace browser interaction or human explanation review.']
    output = ROOT / 'evaluation/results/current_pipeline/runtime_verification.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results, indent=2) + '\n')
    print(json.dumps({k: v for k, v in results.items() if k not in ('curated_demo', 'curated_portfolio')}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--frontend-url')
    run(parser.parse_args().frontend_url)
