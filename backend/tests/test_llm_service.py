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
        self.assertIn('-1200 kWh/year', response.explanation)
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
        text, _, mode, _ = await generate_explanation(FakeEngines().result, provider=FakeProvider({'fact_ids': ['f0']}))
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

    async def test_llm_can_extract_complex_intent(self):
        intent, _ = await extract_intent('Skip insulation and install only a heat pump', FakeProvider({
            'intent': 'simulate_retrofit', 'retrofits': ['heat_pump'], 'budget_gbp': None,
            'objective': 'carbon_reduction'}))
        self.assertEqual(intent.retrofits, ['heat_pump'])

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
        self.assertEqual(payload['format'], 'json')

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
