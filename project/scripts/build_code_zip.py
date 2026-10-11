import hashlib
from pathlib import Path
import subprocess
import zipfile

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parent
OUTPUT = PROJECT / 'submission/megathon-code.zip'
EXCLUDED_PARTS = {'.git', '.venv', 'venv', 'node_modules', '__pycache__', '.pytest_cache', 'submission', 'tmp', 'output', 'raw', 'generated'}
EXCLUDED_PREFIXES = ('Data/csv/', 'Data/reports/', 'backend/data/', 'ml/models/', 'ml/fixtures/', 'ml/reports/', 'evaluation/results/', 'evaluation/references/', 'evaluation/reviews/')


def build():
    names = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=ROOT).decode().split('\0')
    files = []
    for name in sorted(set(filter(None, names))):
        path = ROOT / name
        if not path.is_file():
            continue
        if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
            raise ValueError(f'Unexpected symlink or external file: {name}')
        if any(part in EXCLUDED_PARTS or part.startswith('.next') for part in path.relative_to(ROOT).parts):
            continue
        local_name = name.removeprefix('project/')
        if local_name.startswith(EXCLUDED_PREFIXES) or path.suffix.lower() in {'.csv', '.joblib', '.pkl', '.pickle', '.parquet', '.db', '.pyc', '.log'}:
            continue
        if path.name.startswith('.env') and path.name != '.env.example':
            continue
        files.append(path)
    required = {'README.md', 'LICENSE'}
    selected = {str(path.relative_to(ROOT)) for path in files}
    if not required.issubset(selected):
        raise ValueError(f'Missing required files: {sorted(required - selected)}')
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT, 'w', zipfile.ZIP_DEFLATED) as archive:
        directory = zipfile.ZipInfo('deliverables/', date_time=(2026, 1, 1, 0, 0, 0))
        directory.external_attr = 0o40755 << 16
        archive.writestr(directory, '')
        for path in files:
            info = zipfile.ZipInfo(str(path.relative_to(ROOT)), date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    with zipfile.ZipFile(OUTPUT) as archive:
        if archive.testzip() is not None:
            raise ValueError('ZIP verification failed')
    digest = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    OUTPUT.with_suffix('.zip.sha256').write_text(f'{digest}  {OUTPUT.name}\n')
    print(f'Created {OUTPUT} ({len(files)} files; datasets, weights, dependencies and secrets excluded)')
    if not (ROOT / 'deliverables/final_report.pdf').is_file():
        print('Submission still needs deliverables/final_report.pdf (maximum 3 pages).')


if __name__ == '__main__':
    build()
