from pathlib import Path

import pandas as pd
import pytest

from ml.valuation import manifest_splits, validate_snapshot

ROOT = Path(__file__).resolve().parents[2]


def inputs():
    frame = validate_snapshot(pd.read_csv(ROOT / 'Data/csv/properties.csv'))
    manifest = pd.read_csv(ROOT / 'ml/reports/current_snapshot/split_manifest.csv', dtype=str)
    return frame, manifest


def test_manifest_preserves_original_holdouts_even_when_reordered():
    frame, manifest = inputs()
    splits = manifest_splits(frame, manifest.sample(frac=1, random_state=4))
    for name, indices in splits.items():
        assert set(frame.iloc[indices].property_id) == set(manifest.loc[manifest.split == name, 'property_id'])


@pytest.mark.parametrize('case', ['missing', 'extra', 'duplicate', 'customer', 'label', 'leakage'])
def test_bad_manifest_rejected(case):
    frame, manifest = inputs()
    if case == 'missing':
        manifest = manifest.iloc[1:]
    elif case == 'extra':
        manifest.loc[len(manifest)] = ['UNKNOWN', 'UNKNOWN', 'fit']
    elif case == 'duplicate':
        manifest = pd.concat([manifest, manifest.iloc[:1]])
    elif case == 'customer':
        manifest.loc[0, 'customer_id'] = 'WRONG'
    elif case == 'label':
        manifest.loc[0, 'split'] = 'wrong'
    else:
        other = manifest.index[manifest.split != manifest.loc[0, 'split']][0]
        frame.loc[other, 'customer_id'] = frame.loc[0, 'customer_id']
        manifest.loc[other, 'customer_id'] = frame.loc[0, 'customer_id']
    with pytest.raises(ValueError):
        manifest_splits(frame, manifest)
