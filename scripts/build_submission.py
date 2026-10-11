"""Build a small, explicit, secret-free submission ZIP with checksums."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_SUFFIXES = {'.js', '.sql', '.py', '.ts', '.tsx', '.css', '.json', '.csv', '.md', '.txt', '.ini', '.toml', '.svg', '.xml', '.joblib', '.log', '.jpg'}
EXCLUDED = {'.git', '.venv', '__pycache__', '.pytest_cache', 'node_modules', '.next', '.codex', '.agents', 'generated', 'raw'}


def build(output=ROOT/'submission/greenprint-team-254.zip'):
    models = ['ml/models/snapshot.joblib', 'ml/models/london_snapshot.joblib', 'ml/models/synthetic_impact.joblib']
    london_data = ['Data/generated/kew_london_v3/' + name for name in ['properties.csv', 'energy_usage.csv', 'split_manifest.csv', 'FINAL_EVALUATION.json']]
    required = models + london_data + ['backend/app/db/migrations/001_recommendation_snapshots.sql', 'ml/reports/synthetic_impact/held_out_predictions.csv',
                        'evaluation/results/held_out_retrofits/metrics.json', 'docs/improvement_report.md']
    absent = [name for name in required if not (ROOT/name).is_file()]
    if absent:
        raise ValueError('Generate submission prerequisites first: '+', '.join(absent))
    paths = set()
    directories = ['backend/app', 'backend/tests', 'backend/data', 'carbon_engine', 'frontend/app',
        'frontend/components', 'frontend/lib', 'frontend/tests', 'frontend/public', 'Data', 'scripts',
        'ml/tests', 'ml/fixtures', 'ml/reports/snapshot', 'ml/reports/london_snapshot', 'ml/reports/synthetic_impact', 'evaluation/results/london_active', 'evaluation/tests',
        'evaluation/reviews', 'evaluation/references', 'evaluation/results/held_out_retrofits', 'evaluation/results/current_pipeline']
    for directory in directories:
        for path in (ROOT/directory).rglob('*'):
            if path.is_file() and path.suffix in ALLOWED_SUFFIXES and not any(p in EXCLUDED for p in path.parts):
                paths.add(path)
    for directory in ['ml', 'evaluation', 'frontend', 'backend']:
        for path in (ROOT/directory).glob('*'):
            if path.is_file() and path.suffix in ALLOWED_SUFFIXES and path.name != 'next-env.d.ts':
                paths.add(path)
    for name in ['README.md', 'prd.md', '.python-version', '.node-version', 'docs/reproducibility.md', '.env.example', '.gitignore', 'pytest.ini', 'conftest.py', 'requirements.lock.txt',
                 'backend/catalog.json', 'docs/backend_architecture.md', 'docs/scoring_methodology.md',
                 'docs/valuation_methodology.md', 'docs/synthetic_impact_methodology.md', 'docs/llm_methodology.md',
                 'docs/responsible_ai.md', 'docs/submission_guide.md', 'docs/improvement_report.md', *models, *london_data]:
        paths.add(ROOT/name)
    # Files selected from allowlisted directories must not follow external symlinks.
    for path in paths:
        if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
            raise ValueError('External or symlinked submission input: '+str(path))
    manifest = {'team_number': 254, 'scope': 'synthetic hackathon prototype',
        'files': [{'path': str(p.relative_to(ROOT)), 'size_bytes': p.stat().st_size,
                   'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(paths)],
        'limitations': ['No observed-market or measured retrofit accuracy claim.', 'Human advisor review remains pending.']}
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix('.zip.tmp')
    try:
        with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(paths):
                archive.write(path, str(path.relative_to(ROOT)))
            archive.writestr('SUBMISSION_MANIFEST.json', json.dumps(manifest, indent=2)+'\n')
        with zipfile.ZipFile(temporary) as archive:
            assert archive.testzip() is None
            for row in manifest['files']:
                assert hashlib.sha256(archive.read(row['path'])).hexdigest() == row['sha256']
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix('.zip.sha256').write_text(digest+'  '+output.name+'\n')
    print(json.dumps({'bundle': str(output), 'files': len(paths), 'bytes': output.stat().st_size, 'sha256': digest}, indent=2))
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path, default=ROOT/'submission/greenprint-team-254.zip')
    build(parser.parse_args().output)
