"""Regenerate, verify, then package. Fails immediately on any nonzero exit."""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    os.chdir(ROOT)
    for line in (ROOT / 'requirements.lock.txt').read_text().splitlines():
        if '==' in line:
            name, expected = line.strip().split('==')
            try:
                actual = importlib.metadata.version(name)
            except importlib.metadata.PackageNotFoundError:
                raise SystemExit(f'{name} is missing; install requirements.lock.txt first') from None
            if actual != expected:
                raise SystemExit(f'{name}: expected {expected}, installed {actual}; install requirements.lock.txt first')
    output = ROOT/'evaluation/results/current_pipeline'
    output.mkdir(parents=True, exist_ok=True)
    commands = [
        [sys.executable, 'scripts/prepare_london_demo.py'],
        [sys.executable, '-m', 'ml.train_valuation', '--data', 'Data/csv/properties.csv', '--provenance', 'ml/snapshot_provenance.json', '--target-kind', 'snapshot', '--seed', '42', '--output', 'ml/models/snapshot.joblib', '--reports', 'ml/reports/snapshot'],
        [sys.executable, '-m', 'ml.synthetic_impact'],
        [sys.executable, 'scripts/prepare_demo.py'],
        [sys.executable, '-m', 'evaluation.held_out_retrofits'],
        [sys.executable, '-m', 'evaluation.verify_reference_cases'],
        [sys.executable, '-m', 'evaluation.verify_runtime'],
        [sys.executable, '-m', 'evaluation.verify_london_workflow'],
        [sys.executable, '-m', 'evaluation.reproducibility'],
        [sys.executable, '-m', 'pytest', '-q', '--junitxml=evaluation/results/current_pipeline/tests.xml'],
        [sys.executable, '-m', 'pip', 'check'],
        ['npm', '--prefix', 'frontend', 'run', 'typecheck'],
        ['npm', '--prefix', 'frontend', 'test'],
        ['npm', '--prefix', 'frontend', 'run', 'build'],
    ]
    report = {'python': platform.python_version(), 'node': subprocess.check_output(['node', '--version'], text=True).strip(),
              'scope': 'synthetic prototype and documented-rule agreement', 'steps': []}
    with tempfile.TemporaryDirectory(prefix='greenprint-verification-') as temp:
        env = {**{key: value for key, value in os.environ.items() if not key.startswith(('GREENPRINT_', 'VALUATION_', 'LLM_', 'OLLAMA_'))},
               'PYTHONHASHSEED': '0', 'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1',
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
    paths = ['requirements.lock.txt', 'frontend/package-lock.json', 'Data/csv/properties.csv',
             'Data/csv/energy_usage.csv', 'Data/csv/emission_factors_2026.csv',
             'backend/data/curated_demo_properties.json', 'ml/models/snapshot.joblib',
             'ml/models/synthetic_impact.joblib', 'ml/reports/snapshot/split_manifest.csv',
             'ml/reports/synthetic_impact/split_manifest.csv', 'evaluation/references/runtime_outputs.json']
    report['sha256'] = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths}
    report['git_commit'] = None
    report['working_tree_dirty'] = None
    if (ROOT.parent / '.git').exists():
        report['git_commit'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
        report['working_tree_dirty'] = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip())
    report['training_seeds'] = {'snapshot': 42, 'synthetic_impact': 254}
    (output/'submission_verification.json').write_text(json.dumps(report, indent=2)+'\n')
    try:
        subprocess.run([sys.executable, 'scripts/build_submission.py'], cwd=ROOT, check=True)
        with tempfile.TemporaryDirectory(prefix='greenprint-extracted-') as extracted:
            with zipfile.ZipFile(ROOT / 'submission/greenprint-team-254.zip') as archive:
                archive.extractall(extracted)
            subprocess.run([sys.executable, '-m', 'evaluation.reproducibility'], cwd=Path(extracted) / 'project', check=True)
        report['extracted_bundle_reference_check'] = 'passed'
        (output/'submission_verification.json').write_text(json.dumps(report, indent=2)+'\n')
    except subprocess.CalledProcessError:
        report['status'] = 'failed'
        report['failure'] = 'Submission packaging or extracted-bundle verification failed'
        (output/'submission_verification.json').write_text(json.dumps(report, indent=2)+'\n')
        raise


if __name__ == '__main__':
    main()
