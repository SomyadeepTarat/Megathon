"""Load simple project-root .env settings without evaluating shell code."""
import os
from pathlib import Path
import re
import shlex


def load_project_environment():
    path = Path(__file__).resolve().parents[3] / '.env'
    if not path.is_file():
        return
    for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('export '):
            line = line[7:].strip()
        key, separator, value = line.partition('=')
        key = key.strip()
        if not separator or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', key):
            raise ValueError(f'Invalid .env setting on line {number}')
        try:
            values = shlex.split(value.strip(), comments=True, posix=True)
        except ValueError:
            raise ValueError(f'Invalid .env quoting on line {number}') from None
        if len(values) > 1:
            raise ValueError(f'Quote .env values containing spaces on line {number}')
        # Explicit shell configuration takes precedence. No interpolation/exec.
        os.environ.setdefault(key, values[0] if values else '')
