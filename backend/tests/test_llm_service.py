"""Offline behavioral checks. Fixtures are test evidence, never production estimates."""
import asyncio
import unittest

from pydantic import ValidationError
from backend.app.services.llm_service import (
    AdvisorService, ChatRequest, EngineUnavailable, Intent, extract_intent,
    generate_explanation, OllamaProvider,
)


class FakeEngines:
    def __init__(self):
        self.calls = []
        self.feasible = {'all_feasible': True, 'rejected_retrofits': []}
        self.result = {'property_id': 'P1', 'status': 'success',
                       'feasibility': {'all_feasible': True, 'rejected_retrofits': []},
                       'score': {'baseline': 38, 'after': 72},
                       'energy': {'electricity_savings_kwh': -1200, 'gas_savings_kwh': 9000},
                       'carbon': {'status': 'awaiting_factors', 'reduction_kg_co2e': None},
                       'valuation': {'status': 'unavailable'},
                       'assumptions': ['Synthetic test fixture.'], 'warnings': ['Roof survey required.']}

    async def assessment(self, pid):
        self.calls.append(('assessment', pid))
        return self.result

    async def feasibility(self, pid, retrofits):
        self.calls.append(('feasibility', list(retrofits)))
        return self.feasible

    async def simulate(self, pid, retrofits, budget, objective):
        self.calls.append(('simulate', list(retrofits), budget, objective))
        return self.result

    async def optimize(self, pid, budget, objective):
        self.calls.append(('optimize', budget, objective))
        return self.result


class FakeProvider:
    def __init__(self, response=None, fail=False):
        self.response, self.fail = response, fail
    async def complete(self, system, payload):
        if self.fail:
            raise TimeoutError('test')
        return self.response


class AdvisorTests(unittest.IsolatedAsyncioTestCase):
    async def ask(self, message, **kwargs):
        self.engines = FakeEngines()
        return await AdvisorService(self.engines, **kwargs).chat(ChatRequest(property_id='P1', message=message))

    async def test_heat_pump_simulates_before_explaining(self):
        response = await self.ask('What if I install only a heat pump?')
        self.assertEqual(response.tool_calls, ['feasibility', 'simulate'])
        self.assertEqual(self.engines.calls[1][1], ['heat_pump'])
        self.assertIn('-1,200 kWh/year', response.explanation)
        self.assertIn('increased consumption', response.explanation)

    async def test_two_upgrades(self):
        response = await self.ask('What happens if I install solar panels and a heat pump?')
        self.assertEqual(set(response.intent.retrofits), {'solar_panels', 'heat_pump'})

    async def test_all_five_aliases(self):
        for phrase, retrofit in [('insulation', 'loft_insulation'), ('solar', 'solar_panels'),
                                ('double glazing', 'double_glazing'), ('smart thermostat', 'smart_thermostat')]:
            with self.subTest(phrase=phrase):
                response = await self.ask('What if I install only ' + phrase + '?')
                self.assertEqual(response.intent.retrofits, [retrofit])

    async def test_budget_optimization(self):
        response = await self.ask('What if I have only £5,000?')
        self.assertEqual(response.tool_calls, ['optimize'])
        self.assertEqual(response.intent.budget_gbp, 5000)

    async def test_zero_budget_preserved(self):
        response = await self.ask('budget £0')
        self.assertEqual(response.intent.budget_gbp, 0)

    async def test_ambiguous_scenarios_never_assess(self):
        for question in ['What if I skip insulation and install only a heat pump?',
                         'What if I remove it?', 'What if I install a battery?',
                         'Compare solar versus insulation', 'What if I have £5k?',
                         'What combination reduces carbon emissions the most?',
                         'Should I install solar?', 'What if I install solar without insulation?']:
            with self.subTest(question=question):
                response = await self.ask(question)
                self.assertEqual(response.status, 'clarification_required')
                self.assertEqual(self.engines.calls, [])

    async def test_explanation_uses_current_server_assessment(self):
        response = await self.ask('Why is my score low?')
        self.assertEqual(response.tool_calls, ['assessment'])
        self.assertIn('38 points', response.explanation)

    async def test_simple_explanations_do_not_depend_on_model_intent_guess(self):
        for question in ['Why is my score low?', 'How is carbon calculated?',
                         'Why does electricity use increase with a heat pump?',
                         'Does the model prove a causal premium?', 'Why is valuation unavailable?']:
            with self.subTest(question=question):
                response = await self.ask(question, provider=FakeProvider(response={
                    'intent': 'clarify', 'retrofits': [], 'budget_gbp': None, 'objective': 'carbon_reduction'}))
                self.assertEqual(response.tool_calls, ['assessment'])

    async def test_natural_budget_and_combination_requests(self):
        response = await self.ask('What can I do with a £5000 budget?')
        self.assertEqual(response.tool_calls, ['optimize'])
        self.assertEqual(response.intent.budget_gbp, 5000)
        response = await self.ask('What if I combine insulation and glazing?')
        self.assertEqual(response.tool_calls, ['feasibility', 'simulate'])

    async def test_model_cannot_explain_baseline_instead_of_optimizing(self):
        response = await self.ask('Which package saves most carbon?', provider=FakeProvider(response={
            'intent': 'explain', 'retrofits': [], 'budget_gbp': None, 'objective': 'carbon_reduction'}))
        self.assertEqual(response.status, 'clarification_required')
        self.assertEqual(self.engines.calls, [])

    async def test_infeasible_blocks_simulation(self):
        engines = FakeEngines()
        engines.feasible = {'all_feasible': False, 'rejected_retrofits': ['solar_panels']}
        response = await AdvisorService(engines).chat(ChatRequest(property_id='P1', message='install solar'))
        self.assertEqual(response.status, 'infeasible')
        self.assertEqual(response.tool_calls, ['feasibility'])

    async def test_unknown_feasibility_is_conditional(self):
        engines = FakeEngines()
        engines.feasible = {}
        response = await AdvisorService(engines).chat(ChatRequest(property_id='P1', message='install solar'))
        self.assertEqual(response.status, 'conditional')

    async def test_conditional_list_blocks_even_all_feasible(self):
        engines = FakeEngines()
        engines.feasible['conditional_retrofits'] = ['solar_panels']
        response = await AdvisorService(engines).chat(ChatRequest(property_id='P1', message='install solar'))
        self.assertEqual(response.status, 'conditional')

    async def test_provider_error_falls_back(self):
        response = await self.ask('Why is my score low?', provider=FakeProvider(fail=True))
        self.assertEqual(response.mode, 'deterministic')
        self.assertIn('38 points', response.explanation)

    async def test_unsupported_prose_and_numbers_rejected(self):
        text, _, mode, _ = await generate_explanation(FakeEngines().result, provider=FakeProvider({'text': 'Guaranteed £90000 uplift'}))
        self.assertEqual(mode, 'deterministic')
        self.assertNotIn('90000', text)

    async def test_nonexistent_fact_rejected(self):
        _, _, mode, _ = await generate_explanation(FakeEngines().result, provider=FakeProvider({'fact_ids': ['invented']}))
        self.assertEqual(mode, 'deterministic')

    async def test_valid_fact_selection_preserves_caveats(self):
        text, _, mode, _ = await generate_explanation(FakeEngines().result, provider=FakeProvider({'sentences': [{'text': 'Your current score reflects the recorded property details.', 'fact_ids': ['f0']}]}))
        self.assertEqual(mode, 'grounded_llm')
        self.assertIn('Carbon estimate is unavailable', text)
        self.assertIn('Roof survey required', text)
        self.assertIn('causal', text)

    async def test_unavailable_engine(self):
        class Missing(FakeEngines):
            async def assessment(self, pid):
                raise EngineUnavailable()
        response = await AdvisorService(Missing()).chat(ChatRequest(property_id='P1', message='Explain my score'))
        self.assertEqual(response.status, 'unavailable')
        self.assertIsNone(response.result)

    async def test_wrong_property_never_explained(self):
        engines = FakeEngines()
        engines.result['property_id'] = 'OTHER'
        response = await AdvisorService(engines).chat(ChatRequest(property_id='P1', message='Explain my score'))
        self.assertEqual(response.status, 'unavailable')
        self.assertNotIn('38', response.explanation)

    async def test_failed_calculation_never_success(self):
        engines = FakeEngines()
        engines.result['status'] = 'missing_data'
        response = await AdvisorService(engines).chat(ChatRequest(property_id='P1', message='install solar'))
        self.assertEqual(response.status, 'unavailable')

    async def test_partial_scenario_keeps_energy_when_valuation_unavailable(self):
        engines = FakeEngines()
        engines.result['status'] = 'partial'
        response = await AdvisorService(engines).chat(ChatRequest(property_id='P1', message='install heat pump'))
        self.assertEqual(response.status, 'partial')
        self.assertIn('-1,200 kWh/year', response.explanation)
        self.assertIn('Valuation estimate is unavailable', response.explanation)

    async def test_explicit_selection_resolves_negation(self):
        engines = FakeEngines()
        response = await AdvisorService(engines).chat(ChatRequest(property_id='P1',
            message='Skip insulation and install only a heat pump',
            scenario=Intent(intent='simulate_retrofit', retrofits=['heat_pump'])))
        self.assertEqual(response.intent.retrofits, ['heat_pump'])

    async def test_empty_package_is_supported(self):
        engines = FakeEngines()
        response = await AdvisorService(engines).chat(ChatRequest(property_id='P1', message='baseline',
            scenario=Intent(intent='simulate_retrofit', retrofits=[])))
        self.assertEqual(response.tool_calls, ['feasibility', 'simulate'])

    async def test_negation_requires_explicit_selection_even_if_model_claims_valid(self):
        intent, _ = await extract_intent('Skip insulation and install only a heat pump', FakeProvider({
            'intent': 'simulate_retrofit', 'retrofits': ['heat_pump'], 'budget_gbp': None,
            'objective': 'carbon_reduction'}))
        self.assertEqual(intent.intent, 'clarify')

    async def test_invalid_llm_intent_never_executes(self):
        response = await self.ask('What if I install solar?', provider=FakeProvider({'intent': 'execute_shell'}))
        # The simple grammar remains usable independently of broken LLM output.
        self.assertEqual(response.tool_calls, ['feasibility', 'simulate'])
        intent, _ = await extract_intent('What if I replace the boiler?', FakeProvider({'intent': 'execute_shell'}))
        self.assertEqual(intent.intent, 'clarify')

    async def test_infeasible_recommendations_not_rendered(self):
        result = FakeEngines().result
        result['recommendations'] = [{'retrofit': 'solar_panels', 'feasible': False, 'reason': 'Install anyway'}]
        text, _, _, _ = await generate_explanation(result)
        self.assertNotIn('Install anyway', text)

    async def test_schema_rejects_client_results(self):
        with self.assertRaises(ValidationError):
            ChatRequest(property_id='P1', message='Explain', result={'score': 100})

    async def test_schema_rejects_bad_scenarios(self):
        for payload in [{'intent': 'optimize_budget'}, {'intent': 'simulate_retrofit', 'retrofits': ['battery']},
                        {'intent': 'optimize_budget', 'budget_gbp': -1},
                        {'intent': 'simulate_retrofit', 'retrofits': ['heat_pump', 'heat_pump']},
                        {'intent': 'optimize_budget', 'budget_gbp': float('nan')}]:
            with self.subTest(payload=payload), self.assertRaises(ValidationError):
                Intent(**payload)

    async def test_ollama_payload_and_decode(self):
        from unittest.mock import patch, MagicMock
        import json
        context = MagicMock()
        context.__enter__.return_value.read.return_value = json.dumps({'message': {'content': '{"fact_ids":["f0"]}'}}).encode()
        with patch('urllib.request.urlopen', return_value=context) as send:
            answer = await OllamaProvider('test-local').complete('system', {'question': 'test'})
        self.assertEqual(answer, {'fact_ids': ['f0']})
        payload = json.loads(send.call_args.args[0].data)
        self.assertFalse(payload['stream'])
        self.assertEqual(payload['format']['type'], 'object')
        self.assertFalse(payload['format']['additionalProperties'])
        self.assertFalse(payload['think'])

    async def test_llm_cannot_invent_upgrade(self):
        intent, _ = await extract_intent('What if I replace my boiler?', FakeProvider({
            'intent': 'simulate_retrofit', 'retrofits': ['solar_panels']}))
        self.assertEqual(intent.intent, 'clarify')

    async def test_llm_cannot_invent_budget(self):
        intent, _ = await extract_intent('Which package fits my budget?', FakeProvider({
            'intent': 'optimize_budget', 'budget_gbp': 8000}))
        self.assertEqual(intent.intent, 'clarify')

    async def test_optimization_must_confirm_feasibility(self):
        engines = FakeEngines()
        del engines.result['feasibility']
        response = await AdvisorService(engines).chat(ChatRequest(property_id='P1', message='budget £5000'))
        self.assertEqual(response.status, 'unavailable')

    async def test_unavailable_section_cannot_leak_stale_number(self):
        result = FakeEngines().result
        result['carbon']['reduction_kg_co2e'] = 999999
        text, _, _, _ = await generate_explanation(result)
        self.assertNotIn('999999', text)
        self.assertIn('Carbon estimate is unavailable', text)

    async def test_what_if_cannot_be_classified_as_explanation(self):
        intent, _ = await extract_intent('What if I change my heating?', FakeProvider({'intent': 'explain'}))
        self.assertEqual(intent.intent, 'clarify')

    async def test_route_unconfigured_and_not_found(self):
        from fastapi import FastAPI, HTTPException
        from starlette.requests import Request
        from backend.app.api.advisor import router, chat
        from backend.app.services.llm_service import PropertyNotFound
        app = FastAPI()
        app.include_router(router)
        self.assertIn('/advisor/chat', app.openapi()['paths'])
        request = Request({'type': 'http', 'app': app})
        body = ChatRequest(property_id='P1', message='Explain my score')
        with self.assertRaises(HTTPException) as caught:
            await chat(body, request)
        self.assertEqual(caught.exception.status_code, 503)
        class Missing(FakeEngines):
            async def assessment(self, pid):
                raise PropertyNotFound()
        app.state.advisor_service = AdvisorService(Missing())
        with self.assertRaises(HTTPException) as caught:
            await chat(body, request)
        self.assertEqual(caught.exception.status_code, 404)


if __name__ == '__main__':
    unittest.main()

class LiveAdvisorTests(unittest.IsolatedAsyncioTestCase):
    async def test_follow_up_recalculates_previous_package(self):
        engines = FakeEngines()
        response = await AdvisorService(engines).chat(ChatRequest(
            property_id='P1', message='Why does its electricity consumption increase?',
            context=Intent(intent='simulate_retrofit', retrofits=['heat_pump'])))
        self.assertEqual(response.tool_calls, ['feasibility', 'simulate'])
        self.assertEqual(engines.calls[1][1], ['heat_pump'])

    async def test_context_cannot_replace_new_action(self):
        engines = FakeEngines()
        response = await AdvisorService(engines).chat(ChatRequest(
            property_id='P1', message='install solar',
            context=Intent(intent='simulate_retrofit', retrofits=['heat_pump'])))
        self.assertEqual(response.intent.retrofits, ['solar_panels'])

    async def test_progress_tracks_actual_tools(self):
        progress = []
        async def record(message):
            progress.append(message)
        await AdvisorService(FakeEngines()).chat(ChatRequest(
            property_id='P1', message='install heat pump'), progress=record)
        self.assertEqual(len(progress), 4)
        self.assertIn('feasibility', progress[1])
        self.assertIn('Recalculating', progress[2])

    async def test_fallback_focuses_on_requested_topic(self):
        result = FakeEngines().result
        result['simple_payback_years'] = 12.5
        text, facts, _, _ = await generate_explanation(result, 'What is the payback?')
        self.assertTrue(text.startswith('The modeled simple payback is 12.5 years'))
        self.assertIn('Roof survey required', text)
        self.assertIn('Evidence and limitations', text)


def test_stream_emits_progress_then_validated_result():
    import json
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from backend.app.api.advisor import router
    app = FastAPI()
    app.include_router(router)
    app.state.advisor_service = AdvisorService(FakeEngines())
    with TestClient(app) as client:
        response = client.post('/advisor/chat/stream', json={'property_id': 'P1', 'message': 'install heat pump'})
    assert response.status_code == 200
    blocks = response.text.strip().split('\n\n')
    assert blocks[0].startswith('event: progress')
    assert blocks[-1].startswith('event: result')
    answer = json.loads(blocks[-1].split('data: ', 1)[1])
    assert answer['tool_calls'] == ['feasibility', 'simulate']
    assert answer['mode'] == 'deterministic'


def test_stream_reports_missing_property_without_internal_error():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from backend.app.api.advisor import router
    from backend.app.services.llm_service import PropertyNotFound
    class Missing(FakeEngines):
        async def assessment(self, pid):
            raise PropertyNotFound()
    app = FastAPI(); app.include_router(router)
    app.state.advisor_service = AdvisorService(Missing())
    with TestClient(app) as client:
        response = client.post('/advisor/chat/stream', json={'property_id': 'P1', 'message': 'Explain my score'})
    assert 'event: error' in response.text
    assert 'Property not found' in response.text

class PlanningGrammarTests(unittest.IsolatedAsyncioTestCase):
    async def test_currency_plans_preserve_objective_without_model(self):
        intent, _ = await extract_intent('Plan upgrades within 5000 pounds to reduce carbon', None)
        self.assertEqual(intent.intent, 'optimize_budget')
        self.assertEqual(intent.budget_gbp, 5000)
        intent, _ = await extract_intent('My budget is £15000 for energy reduction', None)
        self.assertEqual(intent.objective, 'energy_reduction')

    async def test_failed_unresolved_plan_never_reads_stale_assessment(self):
        engines = FakeEngines()
        result = await AdvisorService(engines, FakeProvider(fail=True)).chat(ChatRequest(
            property_id='P1', message='Plan upgrades for my home'))
        self.assertEqual(result.status, 'clarification_required')
        self.assertEqual(engines.calls, [])

class BlockedConversationTests(unittest.IsolatedAsyncioTestCase):
    async def test_blocked_upgrade_exposes_reason_and_follow_up_rechecks(self):
        engines = FakeEngines()
        engines.feasible = {'all_feasible': False, 'rejected_retrofits': ['heat_pump'],
                            'items': [{'retrofit': 'heat_pump', 'status': 'infeasible', 'reason': 'A heat pump is already installed.'}]}
        service = AdvisorService(engines)
        first = await service.chat(ChatRequest(property_id='P1', message='install heat pump'))
        second = await service.chat(ChatRequest(property_id='P1', message='what do you mean', context=first.intent))
        self.assertIn('already installed', first.explanation)
        self.assertIn('already installed', second.explanation)
        self.assertEqual(second.status, 'infeasible')
        self.assertEqual(second.tool_calls, ['feasibility'])
        self.assertIsNone(second.clarification_kind)
        self.assertNotIn('simulate', [call[0] for call in engines.calls])

    async def test_missing_budget_asks_amount_not_package(self):
        engines = FakeEngines()
        result = await AdvisorService(engines).chat(ChatRequest(property_id='P1',
            message="what if i don't have enough budget?", context=Intent(intent='simulate_retrofit', retrofits=['heat_pump'])))
        self.assertEqual(result.status, 'clarification_required')
        self.assertEqual(result.clarification_kind, 'budget')
        self.assertIn('maximum you can spend', result.explanation)
        self.assertEqual(engines.calls, [])
        next_answer = await AdvisorService(engines).chat(ChatRequest(property_id='P1', message='budget £5000'))
        self.assertEqual(next_answer.tool_calls, ['optimize'])

    async def test_unclear_package_still_requires_selection(self):
        result = await AdvisorService(FakeEngines()).chat(ChatRequest(property_id='P1', message='remove it'))
        self.assertEqual(result.clarification_kind, 'package')


def test_demo_p00003_reports_existing_heat_pump_on_follow_up(monkeypatch):
    from pathlib import Path
    from fastapi.testclient import TestClient
    from app import main
    from app.db.repository import JsonPropertyRepository
    from app.services.llm_service import AdvisorService as MountedService
    from app.services.advisor_adapter import BackendAdvisorEngines
    root = Path(__file__).resolve().parents[2]
    repository = JsonPropertyRepository(root / 'backend/data/curated_demo_properties.json')
    service = MountedService(BackendAdvisorEngines(lambda: repository, main.get_retrofit_engine,
                                                  main.get_carbon_engine, main.get_valuation_engine))
    monkeypatch.setattr(main.app.state, 'advisor_service', service)
    with TestClient(main.app) as client:
        first = client.post('/advisor/chat', json={'property_id': 'DEMO-P00003', 'message': 'install heat pump'}).json()
        assert first['status'] == 'infeasible'
        assert 'already' in first['explanation'].lower()
        second = client.post('/advisor/chat', json={'property_id': 'DEMO-P00003', 'message': 'what do you mean', 'context': first['intent']}).json()
        assert second['explanation'] == first['explanation']
        assert second['tool_calls'] == ['feasibility']

class ImprovementRoutingTests(unittest.IsolatedAsyncioTestCase):
    async def test_score_improvement_uses_recommendation_tool(self):
        class RecommendationEngines(FakeEngines):
            async def recommendations(self, pid):
                self.calls.append(('recommendations', pid))
                result = self.result.copy()
                result['recommendations'] = [
                    {'retrofit': 'loft_insulation', 'feasible': True, 'after_score': 45, 'estimated_cost_gbp': 1500},
                    {'retrofit': 'heat_pump', 'feasible': False, 'after_score': 99, 'estimated_cost_gbp': 12500},
                    {'retrofit': 'solar_panels', 'feasible': True, 'after_score': None, 'estimated_cost_gbp': 6500}]
                return result
        engines = RecommendationEngines()
        response = await AdvisorService(engines).chat(ChatRequest(property_id='P1', message='how do i improve my score'))
        self.assertEqual(response.intent.intent, 'recommend')
        self.assertEqual(response.tool_calls, ['recommendations'])
        main = response.explanation.split('\n\nEvidence')[0]
        self.assertIn('38 → 45 points', main)
        self.assertNotIn('99', main)
        self.assertIn('Score impact is unavailable for solar panels', main)


def test_demo_p00005_improvement_answer_uses_actual_recommendation_scores(monkeypatch):
    from pathlib import Path
    from fastapi.testclient import TestClient
    from app import main
    from app.db.repository import JsonPropertyRepository
    from app.services.llm_service import AdvisorService as MountedService
    from app.services.advisor_adapter import BackendAdvisorEngines
    repository = JsonPropertyRepository(Path(__file__).resolve().parents[2] / 'backend/data/curated_demo_properties.json')
    monkeypatch.setattr(main.app.state, 'advisor_service', MountedService(BackendAdvisorEngines(
        lambda: repository, main.get_retrofit_engine, main.get_carbon_engine, main.get_valuation_engine)))
    with TestClient(main.app) as client:
        response = client.post('/advisor/chat', json={'property_id': 'DEMO-P00005', 'message': 'how do i improve my score'}).json()
    assert response['intent']['intent'] == 'recommend'
    assert response['tool_calls'] == ['recommendations']
    answer = response['explanation'].split('\n\nEvidence')[0]
    assert 'Feasible options to explore' in answer
    assert 'Tell me your budget' in answer
    for rec in response['result']['recommendations']:
        if rec['after_score'] is not None and rec['retrofit'].replace('_', ' ').capitalize() + ':' in answer:
            assert f"32 → {rec['after_score']:g} points" in answer
