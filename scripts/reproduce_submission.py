"""Regenerate, verify, then package. Fails immediately on any nonzero exit."""
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    output = ROOT/'evaluation/results/current_pipeline'
    output.mkdir(parents=True, exist_ok=True)
    commands = [
        [sys.executable, '-m', 'ml.train_valuation', '--data', 'Data/csv/properties.csv', '--provenance', 'ml/snapshot_provenance.json', '--target-kind', 'snapshot', '--output', 'ml/models/snapshot.joblib', '--reports', 'ml/reports/snapshot'],
        [sys.executable, '-m', 'ml.synthetic_impact'],
        [sys.executable, 'scripts/prepare_demo.py'],
        [sys.executable, '-m', 'evaluation.held_out_retrofits'],
        [sys.executable, '-m', 'evaluation.verify_reference_cases'],
        [sys.executable, '-m', 'evaluation.verify_runtime'],
        [sys.executable, '-m', 'pytest', '-q', '--junitxml=evaluation/results/current_pipeline/tests.xml'],
        [sys.executable, '-m', 'pip', 'check'],
        ['npm', '--prefix', 'frontend', 'run', 'typecheck'],
        ['npm', '--prefix', 'frontend', 'test'],
        ['npm', '--prefix', 'frontend', 'run', 'build'],
    ]
    report = {'python': platform.python_version(), 'node': subprocess.check_output(['node', '--version'], text=True).strip(),
              'scope': 'synthetic prototype and documented-rule agreement', 'steps': []}
    with tempfile.TemporaryDirectory(prefix='greenprint-verification-') as temp:
        env = {**os.environ, 'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1',
               'GREENPRINT_DB_PATH': str(Path(temp)/'properties.db'), 'GREENPRINT_PROPERTY_DATASET': 'csv',
               'LLM_PROVIDER': 'deterministic'}
        for index, command in enumerate(commands):
            log = output/f'reproduction-{index+1:02}.log'
            print('Running: '+' '.join(command), flush=True)
            with log.open('w') as stream:
                result = subprocess.run(command, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT)
            report['steps'].append({'command': command, 'exit_code': result.returncode, 'log': str(log.relative_to(ROOT))})
            report['status'] = 'passed' if result.returncode == 0 else 'failed'
            (output/'submission_verification.json').write_text(json.dumps(report, indent=2)+'\n')
            if result.returncode:
                print(log.read_text()[-6000:])
                raise SystemExit(result.returncode)
    subprocess.run([sys.executable, 'scripts/build_submission.py'], cwd=ROOT, check=True)


if __name__ == '__main__':
    main()
