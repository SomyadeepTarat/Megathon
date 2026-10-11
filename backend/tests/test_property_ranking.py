from pathlib import Path

from app.db.repository import JsonPropertyRepository
from app.services.p4_adapter import P4RetrofitAdapter, P4CarbonAdapter
from app.services.portfolio import rank_portfolio
from app.schemas.engines import ValuationResult


class UnavailableValuation:
    def predict_value_impact(self, before, after):
        return ValuationResult(status='unavailable', reason='No valuation artifact')


def test_property_rank_uses_package_energy_and_preserves_values():
    repository = JsonPropertyRepository(Path(__file__).resolve().parents[1] / 'data/curated_demo_properties.json')
    records = repository.list_properties()
    rows = rank_portfolio(repository, P4RetrofitAdapter(), P4CarbonAdapter(), UnavailableValuation())
    indexed = {record.property.property_id: record for record in records}
    available = [row for row in rows if row.improvement is not None]
    assert available
    assert [row.improvement for row in available] == sorted([row.improvement for row in available], reverse=True)
    for row in rows:
        record = indexed[row.property_id]
        assert row.current_property_value_gbp == record.property.current_property_value_gbp
        assert row.poor_home == (row.score < 50 if row.score is not None else None)
        if row.improvement is not None:
            total = record.annual_energy.electricity_kwh + record.annual_energy.gas_kwh
            assert abs(row.improvement - 100 * (row.electricity_savings_kwh + row.gas_savings_kwh) / total) < 1e-8
            assert row.rank is not None
        else:
            assert row.rank is None
            assert row.reason


def test_missing_and_zero_baselines_remain_unranked():
    repository = JsonPropertyRepository(Path(__file__).resolve().parents[1] / 'data/curated_demo_properties.json')
    records = repository.list_properties()[:2]
    records[0].annual_energy.electricity_kwh = None
    records[1].annual_energy.electricity_kwh = 0
    records[1].annual_energy.gas_kwh = 0
    class Repository:
        def list_properties(self):
            return records
    rows = rank_portfolio(Repository(), P4RetrofitAdapter(), P4CarbonAdapter(), UnavailableValuation())
    assert all(row.rank is None and row.improvement is None and row.reason for row in rows)


def test_ranking_route_is_not_treated_as_property_id():
    from fastapi.testclient import TestClient
    from app.main import app, get_repository
    repository = JsonPropertyRepository(Path(__file__).resolve().parents[1] / 'data/curated_demo_properties.json')
    app.dependency_overrides[get_repository] = lambda: repository
    try:
        response = TestClient(app).get('/properties/ranking')
        assert response.status_code == 200
        assert len(response.json()) == len(repository.list_properties())
        assert 'rank' in response.json()[0]
        assert 'current_property_value_gbp' in response.json()[0]
    finally:
        app.dependency_overrides.pop(get_repository, None)


def test_identical_potential_shares_rank():
    repository = JsonPropertyRepository(Path(__file__).resolve().parents[1] / 'data/curated_demo_properties.json')
    first = repository.list_properties()[0]
    second = first.model_copy(deep=True)
    second.property.property_id = 'SAME-POTENTIAL'
    class Repository:
        def list_properties(self):
            return [second, first]
    rows = rank_portfolio(Repository(), P4RetrofitAdapter(), P4CarbonAdapter(), UnavailableValuation())
    assert [row.rank for row in rows] == [1, 1]
    assert rows[0].property_id == first.property.property_id
