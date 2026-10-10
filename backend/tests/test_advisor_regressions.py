"""Audit regressions, including the real mounted route with production dependencies."""
import json
import unittest
from unittest.mock import MagicMock, patch

from app.services.llm_service import OllamaProvider, extract_intent, generate_explanation


class HostileProvider:
    async def complete(self, system, payload):
        return {'intent': 'simulate_retrofit', 'retrofits': ['heat_pump', 'solar_panels']}


class TransportTests(unittest.IsolatedAsyncioTestCase):
    async def test_task_specific_fact_schema(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({
            'message': {'content': '{"fact_ids":["f0"]}'}, 'done_reason': 'stop'}).encode()
        with patch('urllib.request.urlopen', return_value=response) as send:
            result = await OllamaProvider('qwen3:4b').complete('select evidence', {
                'facts': [{'id': 'f0', 'text': 'Test evidence', 'source': 'test'}]})
        body = json.loads(send.call_args.args[0].data)
        self.assertFalse(body['think'])
        self.assertEqual(body['format']['properties']['fact_ids']['items']['enum'], ['f0'])
        self.assertEqual(body['format']['required'], ['fact_ids'])
        self.assertEqual(result, {'fact_ids': ['f0']})

    async def test_empty_and_truncated_outputs_rejected(self):
        for envelope in [{'message': {'content': '', 'thinking': 'hidden'}, 'done_reason': 'length'},
                         {'message': {'content': ''}, 'done_reason': 'stop'},
                         {'message': {'content': '[]'}, 'done_reason': 'stop'}]:
            response = MagicMock()
            response.__enter__.return_value.read.return_value = json.dumps(envelope).encode()
            with self.subTest(envelope=envelope), patch('urllib.request.urlopen', return_value=response):
                with self.assertRaises(ValueError):
                    await OllamaProvider('qwen3:4b').complete('intent', {'question': 'test'})

    async def test_negation_and_comparison_guard_does_not_trust_model(self):
        for question in ["Install a heat pump but not solar panels", "Don't install solar; add a heat pump",
                         'Heat pump without solar panels', 'Skip solar panels and install a heat pump',
                         'Compare heat pump versus solar panels', 'Install heat pump instead of solar panels',
                         'Keep my gas boiler and add solar panels', 'Either a heat pump or solar panels',
                         'Install solar panels or a heat pump']:
            with self.subTest(question=question):
                intent, reason = await extract_intent(question, HostileProvider())
                self.assertEqual(intent.intent, 'clarify')
                self.assertEqual(reason, 'ambiguous_package')

    async def test_components_render_as_readable_evidence(self):
        text, _, _, _ = await generate_explanation({'score': {'components': [
            {'name': 'insulation', 'subscore': 20, 'contribution': 3.0, 'weight': .15,
             'evidence': {'insulation': 'poor'}},
            {'name': 'consumption', 'subscore': None, 'contribution': None, 'evidence': {}}]},
            'valuation': {'status': 'unavailable'}})
        self.assertIn('Insulation: subscore 20; weighted contribution 3.0 points.', text)
        self.assertIn('insulation: poor', text)
        self.assertNotIn('"subscore"', text)
        self.assertIn('Consumption: this score component is unavailable', text)

    async def test_available_after_score_survives_missing_baseline_score(self):
        text, _, _, _ = await generate_explanation({'score': {
            'status': 'unavailable', 'baseline': None, 'after_status': 'available', 'after': 72}})
        self.assertIn('Post-retrofit Green Home Score: 72 points', text)


class MountedRouteTests(unittest.TestCase):
    def setUp(self):
        from fastapi.testclient import TestClient
        from app.main import app
        self.client = TestClient(app)

    def test_actual_route_explains_partial_assessment(self):
        properties = self.client.get('/properties').json()
        pid = properties[0]['property_id']
        response = self.client.post('/advisor/chat', json={'property_id': pid, 'message': 'Explain my score'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn(data['status'], ('success', 'partial'))
        self.assertEqual(data['tool_calls'], ['assessment'])
        self.assertEqual(data['result']['property_id'], pid)
        self.assertIn('Property dataset: synthetic', data['explanation'])

    def test_actual_route_reports_missing_scenario_engine(self):
        pid = self.client.get('/properties').json()[0]['property_id']
        response = self.client.post('/advisor/chat', json={'property_id': pid, 'message': 'Install heat pump'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'unavailable')
        self.assertIsNone(response.json()['result'])

    def test_actual_route_missing_property_and_validation(self):
        response = self.client.post('/advisor/chat', json={'property_id': 'DOES_NOT_EXIST', 'message': 'Explain my score'})
        self.assertEqual(response.status_code, 404)
        response = self.client.post('/advisor/chat', json={'property_id': 'P1', 'message': ' '})
        self.assertEqual(response.status_code, 422)

    def test_scenario_adapter_preserves_partial_energy(self):
        from app.schemas.engines import ScenarioResponse, FeasibilityResult, FeasibilityItem, EnergyImpact, FuelState, CarbonResult, ValuationResult
        from app.services.advisor_adapter import scenario_view
        from app.main import repository
        from app.core.efficiency import assess
        row = repository.list_properties()[0]
        baseline = assess(row)
        scenario = ScenarioResponse(scenario_id='audit-test', property_id=row.property.property_id,
            status='partial', baseline_assessment=baseline,
            feasibility=FeasibilityResult(status='available', items=[
                FeasibilityItem(retrofit='heat_pump', status='feasible', reason='Synthetic regression fixture')]),
            energy=EnergyImpact(baseline=FuelState(electricity_kwh=1000, gas_kwh=1000),
                                after=FuelState(electricity_kwh=1200, gas_kwh=0),
                                electricity_savings_kwh=-200, gas_savings_kwh=1000,
                                net_savings_kwh=800, improvement_percentage=40),
            carbon=CarbonResult(status='unavailable', reason='No official factors in test'),
            valuation=ValuationResult(status='unavailable', reason='No model in test'))
        result = scenario_view(scenario, ['heat_pump'])
        self.assertEqual(result['status'], 'partial')
        self.assertEqual(result['energy']['electricity_savings_kwh'], -200)
        self.assertTrue(result['feasibility']['all_feasible'])
        import asyncio
        text, _, _, _ = asyncio.run(generate_explanation(result))
        self.assertIn('-200.0 kWh/year', text)
        self.assertIn('Valuation estimate is unavailable', text)
