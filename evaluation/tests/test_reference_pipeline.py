from evaluation.verify_reference_cases import run


def test_hand_calculated_references_and_missing_infeasible_cases():
    report = run()
    assert len(report['cases']) == 12
    assert max(report['per_fuel_mae_kwh'].values()) < 1e-8
