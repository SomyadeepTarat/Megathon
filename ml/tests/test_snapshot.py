from pathlib import Path
import joblib
import pandas as pd
import pytest
from ml.valuation import train, validate_data, conformal_radius, chronological_evaluation, NUMERIC, CATEGORICAL
from ml.make_fixture import fixture
from backend.app.services.valuation_service import predict_property_value, predict_value_impact

ROOT = Path(__file__).resolve().parents[2]

@pytest.fixture(scope='module')
def snapshot(tmp_path_factory):
    df = pd.read_csv(ROOT / 'Data/csv/properties.csv')
    artifact, report, _, manifest = train(df, {'kind': 'synthetic', 'source': 'test', 'license': 'test'}, target_kind='snapshot')
    path = tmp_path_factory.mktemp('snapshot') / 'model.joblib'
    joblib.dump(artifact, path)
    normalized = df.rename(columns={'floor_area_m2': 'floor_area'})
    state = next(row.to_dict() for _, row in normalized.iterrows() if all(lo <= row[c] <= hi for c, (lo, hi) in artifact['numeric_bounds'].items()))
    return artifact, report, manifest, path, state


def test_snapshot_contract_and_gates(snapshot):
    artifact, report, manifest, path, state = snapshot
    assert not set(['current_value_estimate_gbp', 'energy_rating', 'market_index']) & set(artifact['features'])
    assert not report['group_overlap']
    assert manifest.groupby('customer_id')['split'].nunique().max() == 1
    assert all(len(v['folds']) == 5 for v in report['grouped_cross_validation'].values())
    assert predict_property_value(state, path)['status'] == 'unavailable'
    result = predict_property_value(state, path, allow_illustrative=True)
    assert result['status'] == 'illustrative'
    assert result == predict_property_value({**state, 'current_value_estimate_gbp': 1}, path, allow_illustrative=True)
    aliases = {**state, 'floor_area_m2': state['floor_area'], 'property_age_years': state['age'], 'property_type': state['property_type'].lower().replace('-', '_')}
    del aliases['floor_area']; del aliases['age']
    assert result == predict_property_value(aliases, path, allow_illustrative=True)
    assert predict_value_impact(state, {**state, 'energy_rating': 'A'}, path, allow_illustrative=True)['status'] == 'unavailable'
    assert predict_property_value({**state, 'floor_area': 1e9}, path, allow_illustrative=True)['status'] == 'unavailable'


def test_baseline_route(snapshot, monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    monkeypatch.setenv('VALUATION_BASELINE_MODEL_PATH', str(snapshot[3]))
    client = TestClient(app)
    prop = snapshot[4]['property_id']
    for method in [client.get, client.post]:
        response = method(f'/properties/{prop}/valuation')
        assert response.status_code == 200
        assert response.json()['status'] == 'illustrative'
    assert client.get('/properties/does-not-exist/valuation').status_code == 404


def test_corrupt_model(tmp_path):
    path = tmp_path / 'bad.joblib'
    joblib.dump({'format_version': 1}, path)
    assert predict_property_value({}, path)['status'] == 'unavailable'


@pytest.mark.parametrize('residuals', [[float('nan')], [-1], [], [[1]]])
def test_invalid_calibration(residuals):
    with pytest.raises(ValueError):
        conformal_radius(residuals, .1)


def test_future_epc_and_time_diagnostic():
    df = fixture()
    df['epc_date'] = pd.to_datetime(df.sale_date) + pd.Timedelta(days=1)
    with pytest.raises(ValueError, match='before sale'):
        validate_data(df)
    df = validate_data(fixture())
    result = chronological_evaluation(df, NUMERIC, NUMERIC + CATEGORICAL + ['energy_rating'], 'sale_price')
    assert result['status'] in {'available', 'unavailable'}
    if result['status'] == 'available':
        assert result['earlier_rows'] + result['later_rows'] + result['excluded_cross_cutoff_rows'] == len(df)


def test_backend_directory_import():
    import subprocess
    import sys
    result = subprocess.run([sys.executable, '-c', 'from app.services.valuation_service import predict_property_value'], cwd=ROOT / 'backend', capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
