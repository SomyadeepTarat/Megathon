"""Reproduce the London cohort and frozen baseline model without inventing evidence."""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    subprocess.run([sys.executable, 'Data/scripts/simulate_london.py', '--total', '2000'], cwd=ROOT, check=True)
    # The delivered final_evaluation file is the already-exposed configuration marker.
    shutil.copyfile(ROOT / 'Data/reports/kew_london_v3/final_evaluation.json',
                    ROOT / 'Data/generated/kew_london_v3/FINAL_EVALUATION.json')
    subprocess.run([sys.executable, '-m', 'ml.train_valuation', '--target-kind', 'snapshot',
        '--data', 'Data/generated/kew_london_v3/properties.csv',
        '--provenance', 'ml/london_snapshot_provenance.json',
        '--split-manifest', 'Data/reports/kew_london_v3/split_manifest.csv',
        '--exclude-split', 'legacy_diagnostic', '--interval-policy', 'price_proportional',
        '--output', 'ml/models/london_snapshot.joblib', '--reports', 'ml/reports/london_snapshot'],
        cwd=ROOT, check=True)


if __name__ == '__main__':
    main()
