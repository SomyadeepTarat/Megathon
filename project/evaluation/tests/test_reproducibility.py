import pytest
from evaluation.reproducibility import compare


def test_reference_comparison_accepts_small_numeric_roundoff():
    compare({'rank': 1, 'energy': [1250.0, None]}, {'rank': 1, 'energy': [1250.0000001, None]})


@pytest.mark.parametrize('actual', [
    {'rank': 2, 'energy': [1250.0, None]},
    {'rank': 1, 'energy': [1251.0, None]},
    {'rank': 1, 'energy': [1250.0, 0]},
    {'rank': 1, 'energy': [1250.0]},
    {'rank': 1, 'energy': [float('nan'), None]},
    {'rank': True, 'energy': [1250.0, None]},
    {'rank': 1, 'energy': [1250.0, None], 'extra': 0},
])
def test_reference_comparison_rejects_changed_results(actual):
    with pytest.raises(ValueError, match='result'):
        compare({'rank': 1, 'energy': [1250.0, None]}, actual)
