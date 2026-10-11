import pytest
from app.services.grounded_language import prepare, render
from app.services.llm_service import Fact

@pytest.fixture
def facts():
    return [Fact(id='f0', text='Score: 32 points.', source='score.baseline'),
            Fact(id='f1', text='Electricity savings: -1200 kWh/year.', source='energy.electricity_savings_kwh'),
            Fact(id='f2', text='Insulation is poor.', source='score.components.insulation')]

def test_natural_prose_resolves_only_backend_owned_slots(facts):
    prepared, slots = prepare(facts)
    answer = {'sentences': [{'text': 'Your score is {{n0}} points, and poor insulation is an area to address.', 'fact_ids': ['f0', 'f2']}]}
    assert render(answer, facts, slots) == 'Your score is 32 points, and poor insulation is an area to address.'
    assert '{{n0}}' in prepared[0]['text']

@pytest.mark.parametrize('text,ids', [
    ('Your score is 99 points.', ['f0']),
    ('Your score is {{n99}} points.', ['f0']),
    ('Your score is {{n1}} points.', ['f0']),
    ('Your score is {{n0}} points.', ['unknown']),
    ('A heat pump guarantees savings.', ['f0']),
    ('Your score is {{missing}}.', ['f0']),
])
def test_invalid_claims_fail_closed(facts, text, ids):
    _, slots = prepare(facts)
    with pytest.raises(ValueError):
        render({'sentences': [{'text': text, 'fact_ids': ids}]}, facts, slots)

def test_negative_saving_keeps_its_sign(facts):
    _, slots = prepare(facts)
    assert '-1200' in render({'sentences': [{'text': 'Electricity savings are {{n1}} kWh/year; the negative sign means consumption increases.', 'fact_ids': ['f1']}]}, facts, slots)

from app.services.grounded_language import render_natural

def test_prose_cannot_relabel_after_score_as_generated_increase(facts):
    with pytest.raises(ValueError):
        render_natural({'sentences': [{'text': 'This could increase your score by 32 points.', 'fact_ids': ['f0']}]}, facts)

def test_spelled_out_estimate_rejected(facts):
    with pytest.raises(ValueError):
        render_natural({'sentences': [{'text': 'This adds five thousand pounds.', 'fact_ids': ['f0']}]}, facts)

def test_backend_metric_sentence_preserves_final_score_meaning():
    facts = [Fact(id='f0', source='recommendations.0', text='Smart thermostat is confirmed feasible. Estimated installation cost: £200. Modeled score after this upgrade alone: 38 points.')]
    answer = {'sentences': [{'text': 'A smart thermostat is feasible for this home.', 'fact_ids': ['f0']}], 'metric_fact_ids': ['f0']}
    text = render_natural(answer, facts)
    assert 'final score of 38 points' in text
    assert 'cost of £200' in text
    assert 'increase' not in text

def test_heat_pump_does_not_reduce_required_thermal_demand(facts):
    with pytest.raises(ValueError):
        render_natural({'sentences': [{'text': 'A heat pump could lower heating demand.', 'fact_ids': ['f2']}]}, facts)

@pytest.mark.parametrize('provider_enabled', [False, True])
def test_baseline_explanation_does_not_confuse_unavailable_uplift(provider_enabled):
    import asyncio
    from app.services.llm_service import generate_explanation
    class IncorrectProvider:
        async def complete(self, prompt, payload):
            return {'sentences': [{'text': 'Your baseline value is unavailable.',
                                   'fact_ids': [payload['answer_facts'][0]['id']]}]}
    result = {'valuation': {'status': 'unavailable', 'reason': 'Synthetic training cannot establish real-world uplift.'},
              'baseline_valuation': {'status': 'illustrative', 'range_gbp': [128627, 560073]}}
    text, _, mode, _ = asyncio.run(generate_explanation(result, 'What is my baseline property value?', IncorrectProvider() if provider_enabled else None))
    assert '£128,627' in text and '£560,073' in text
    assert 'baseline value is unavailable' not in text
    assert 'cannot establish real-world uplift' not in text
    assert mode == 'deterministic'
    impact, _, _, _ = asyncio.run(generate_explanation(result, 'How much could my property value change?'))
    assert 'cannot establish real-world uplift' in impact
