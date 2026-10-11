"""Exercise a running backend's calculated, persisted recommendation flow.

Run from any directory: python /path/to/scripts/verify_recommendation_storage.py
No physical inputs, prices or emission factors are fabricated by this demo.
"""
import argparse
import json
from urllib.parse import quote
from urllib.request import Request, urlopen


def verify(base_url, property_id):
    def call(path, payload=None):
        request = Request(base_url.rstrip('/') + path,
            data=json.dumps(payload).encode() if payload is not None else None,
            headers={'Content-Type': 'application/json'})
        with urlopen(request, timeout=30) as response:
            return json.load(response)

    encoded = quote(property_id, safe='')
    record = call(f'/properties/{encoded}')
    # Dataset metadata belongs to PropertyRecord, not RecommendationRequest.
    payload = {key: value for key, value in record.items()
               if key not in ('dataset_kind', 'dataset_source')}
    payload.update(objective='energy_reduction', scenario_id=f'walkthrough-{property_id}')
    posted = call('/retrofits/recommend', payload)
    path = f"/properties/{encoded}/recommendations?scenario_id={quote(posted['scenario_id'], safe='')}"
    stored = call(path)
    assert posted == stored, 'POST output must match the stored GET output'
    assert stored['property_id'] == property_id
    percentages = [option['scenario']['energy']['improvement_percentage'] for option in stored['recommendations']]
    assert percentages == sorted(percentages, reverse=True)
    assert all(option['feasibility']['status'] == 'feasible' for option in stored['recommendations'])
    for option in stored['recommendations']:
        energy = option['scenario']['energy']
        before, after = energy['baseline'], energy['after']
        total = before['electricity_kwh'] + before['gas_kwh']
        expected = 100 * (total - after['electricity_kwh'] - after['gas_kwh']) / total
        assert abs(expected - energy['improvement_percentage']) < 1e-7
    summary = {key: stored[key] for key in ('property_id', 'scenario_id', 'revision', 'objective', 'status', 'installation_order')}
    summary['recommendations'] = [{'retrofit': option['retrofit'], 'priority': option['priority'],
        'percentage_reduction': option['scenario']['energy']['improvement_percentage'],
        'electricity_savings_kwh': option['scenario']['energy']['electricity_savings_kwh'],
        'gas_savings_kwh': option['scenario']['energy']['gas_savings_kwh'],
        'carbon_savings_kg_co2e': option['scenario']['carbon']['reduction_kg_co2e'],
        'suitability': option['suitability']} for option in stored['recommendations']]
    summary['other_options'] = [{'retrofit': option['retrofit'], 'feasibility': option['feasibility']['status'],
        'reason': option['ranking_reason']} for option in stored['other_options']]
    print(json.dumps(summary, indent=2))
    print('Verified: mounted POST and stored GET return the same ordered results.')
    return stored


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://127.0.0.1:8001')
    parser.add_argument('--property-id', default='P00001')
    args = parser.parse_args()
    verify(args.base_url, args.property_id)
