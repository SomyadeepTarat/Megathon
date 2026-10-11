import pytest
from evaluation.checks import check_energy, check_monotonicity, check_score
from evaluation.evaluate_energy import evaluate as reference_energy
from evaluation.evaluate_explanations import evaluate
from evaluation.evaluate_recommendations import evaluate as feasibility


def energy():
    return {"baseline": {"electricity_kwh": 4800, "gas_kwh": 12000},
            "after": {"electricity_kwh": 6000, "gas_kwh": 3000},
            "savings": {"electricity_kwh": -1200, "gas_kwh": 9000, "net_kwh": 7800, "percentage": 46.428571}}


def test_signed_fuel_savings():
    check_energy(energy())
    bad = energy()
    bad["savings"]["electricity_kwh"] = 1200
    with pytest.raises(AssertionError):
        check_energy(bad)


def test_zero_and_missing():
    result = {"baseline": dict(electricity_kwh=0, gas_kwh=0), "after": dict(electricity_kwh=0, gas_kwh=0),
              "savings": dict(electricity_kwh=0, gas_kwh=0, net_kwh=0, percentage=None)}
    check_energy(result)
    result["baseline"]["gas_kwh"] = None
    with pytest.raises(AssertionError):
        check_energy(result)


def test_monotonicity():
    check_monotonicity(lambda s: {"score": s}, [20, 60, 100])
    with pytest.raises(AssertionError):
        check_monotonicity(lambda s: {"score": s}, [60, 20])


def test_llm_unreviewed_does_not_claim_success():
    result = evaluate([{"case_id": "test", "response": "Electricity savings are -1,200 kWh; value is unavailable.", "allowed_numbers": [-1200]}])
    assert result["targets_met"] is None
    assert result["human_metrics"] is None
    assert result["responses_with_unsupported_numbers_fraction"] == 0
    result = evaluate([{"case_id": "test", "response": "You save £9999", "allowed_numbers": []}])
    assert result["responses_with_unsupported_numbers_fraction"] == 1


def test_feasibility_needs_independent_labels():
    with pytest.raises(ValueError):
        feasibility([{"expected": "eligible", "predicted": "eligible"}])


def test_score_contract_and_bad_weights():
    components = [{"weight": w, "subscore": 100, "contribution": 100*w} for w in [.25,.2,.15,.15,.1,.1,.05]]
    result = {"score": 100, "classification": "Highly efficient", "components": components}
    check_score(result)
    components[0]["weight"] = .24
    with pytest.raises(AssertionError):
        check_score(result)


def test_independent_energy_and_zero_percentage_denominator():
    rows = [{"independently_prepared": True, "reference_source": "hand calculation for harness test",
             "expected_after": {"electricity_kwh": 0, "gas_kwh": 100},
             "predicted_after": {"electricity_kwh": 10, "gas_kwh": 90}}]
    result = reference_energy(rows)
    assert result["per_fuel"]["electricity_kwh"]["mape_percent"] is None
    assert result["per_fuel"]["gas_kwh"]["mae_kwh"] == 10


def test_unfilled_llm_template_is_rejected():
    with pytest.raises(ValueError, match="actual response"):
        evaluate([{"case_id": "pending", "response": None}])


def test_score_verifier_matches_backend_half_up_rounding():
    # Exact 40.5 must round to 41, matching P1's published score method.
    components = [{"weight": w, "subscore": s, "contribution": w*s}
                  for w, s in zip([.25,.2,.15,.15,.1,.1,.05], [40, 77.5, 20, 50, 20, 0, 50])]
    check_score({"score": 41, "classification": "Poor", "components": components})


def test_documented_synthetic_references_are_scoped_separately():
    rows = [{'expected': 'eligible', 'predicted': 'eligible', 'reference_kind': 'documented_rule',
             'reference': 'prd.md section 8', 'label_methodology': 'Known compatible installation'}]
    result = feasibility(rows)
    assert result['scope'] == 'synthetic/reference agreement'
    assert result['limitation'] is not None
    rows[0].pop('label_methodology')
    with pytest.raises(ValueError):
        feasibility(rows)
