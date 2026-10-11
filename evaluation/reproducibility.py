import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / 'evaluation/references/runtime_outputs.json'
INPUTS = ['Data/csv/properties.csv', 'Data/csv/energy_usage.csv', 'Data/csv/emission_factors_2026.csv',
          'Data/csv/emission_factors_2026.provenance.json', 'backend/data/curated_demo_properties.json',
          'ml/snapshot_provenance.json']


def compare(expected, actual, path='result'):
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or expected.keys() != actual.keys():
            raise ValueError(f'{path}: fields differ')
        for key in expected:
            compare(expected[key], actual[key], f'{path}.{key}')
    elif isinstance(expected, list):
        if not isinstance(actual, list) or len(expected) != len(actual):
            raise ValueError(f'{path}: row count differs')
        for index, (before, after) in enumerate(zip(expected, actual)):
            compare(before, after, f'{path}[{index}]')
    elif isinstance(expected, (float, int)) and not isinstance(expected, bool):
        if not isinstance(actual, (float, int)) or isinstance(actual, bool) or not math.isclose(expected, actual, rel_tol=1e-9, abs_tol=1e-6):
            raise ValueError(f'{path}: numerical output differs ({expected} vs {actual})')
    elif type(expected) is not type(actual) or expected != actual:
        raise ValueError(f'{path}: output differs ({expected!r} vs {actual!r})')


def collect():
    for name in ('snapshot.joblib', 'synthetic_impact.joblib'):
        if not (ROOT / 'ml/models' / name).is_file():
            raise ValueError(f'Missing model {name}; regenerate models first')
    sys.path.insert(0, str(ROOT / 'backend'))
    from fastapi.testclient import TestClient
    from app.main import app
    output = {'input_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in INPUTS},
              'assessments': [], 'valuations': [], 'scenarios': []}
    with TestClient(app) as client:
        def get(path):
            response = client.get(path)
            response.raise_for_status()
            return response.json()
        properties = get('/properties')
        for property_row in properties:
            identifier = property_row['property_id']
            output['assessments'].append(get(f'/properties/{identifier}/assessment'))
            output['valuations'].append(get(f'/properties/{identifier}/valuation'))
        output['property_ranking'] = get('/properties/ranking')
        record = get('/properties/DEMO-P00001')
        payload = {key: value for key, value in record.items() if key not in ('dataset_kind', 'dataset_source')}
        for measures in [[], ['loft_insulation'], ['loft_insulation', 'heat_pump', 'solar_panels']]:
            response = client.post('/scenarios/simulate', json={**payload, 'retrofits': measures})
            response.raise_for_status()
            result = response.json()
            output['scenarios'].append({key: result[key] for key in ['status', 'property_id', 'applied_retrofits',
                'baseline_assessment', 'after_assessment', 'energy', 'carbon', 'valuation', 'installation_cost_gbp',
                'annual_bill_savings_gbp', 'simple_payback_years']})
    if not any(row['status'] != 'unavailable' for row in output['valuations']):
        raise ValueError('Reference demo valuation artifacts are missing or unsupported; regenerate models first')
    return output


def run(output, reference=REFERENCE):
    with tempfile.TemporaryDirectory(prefix='greenprint-repeatability-') as directory:
        env = {key: value for key, value in os.environ.items() if not key.startswith(('GREENPRINT_', 'VALUATION_', 'LLM_', 'OLLAMA_'))}
        env.update(GREENPRINT_PROPERTY_DATASET='demo', GREENPRINT_DB_PATH=str(Path(directory) / 'properties.db'),
                   LLM_PROVIDER='deterministic', PYTHONHASHSEED='0', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
        attempts = []
        for index in range(2):
            destination = Path(directory) / f'run-{index}.json'
            env['GREENPRINT_DB_PATH'] = str(Path(directory) / f'properties-{index}.db')
            subprocess.run([sys.executable, '-m', 'evaluation.reproducibility', '--collect', str(destination)],
                           cwd=ROOT, env=env, check=True)
            attempts.append(json.loads(destination.read_text()))
        compare(attempts[0], attempts[1])
        if reference is not None:
            compare(json.loads(Path(reference).read_text()), attempts[0])
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(attempts[0], indent=2, sort_keys=True) + '\n')
        print(json.dumps({'status': 'passed', 'fresh_process_runs': 2, 'reference_checked': reference is not None,
                          'absolute_tolerance': 1e-6, 'relative_tolerance': 1e-9, 'output': str(output)}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--collect', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'evaluation/results/current_pipeline/reproducibility_outputs.json')
    parser.add_argument('--write-reference', action='store_true')
    args = parser.parse_args()
    if args.collect:
        args.collect.write_text(json.dumps(collect(), sort_keys=True))
    elif args.write_reference:
        run(REFERENCE, reference=None)
    else:
        run(args.output)
