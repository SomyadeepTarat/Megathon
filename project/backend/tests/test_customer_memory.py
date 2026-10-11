import asyncio
import copy
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.services.customer_memory import MemoryStore, MemoryUpdate, Preferences, MemoryConflict, identity, MemoryAdvisorService
from app.services.llm_service import ChatRequest
from app.db.repository import JsonPropertyRepository, EditableRepository
from app.services.advisor_adapter import BackendAdvisorEngines
from app.services.p4_adapter import P4RetrofitAdapter, P4CarbonAdapter
from app.services.adapters import ExistingValuationAdapter

ROOT = Path(__file__).resolve().parents[2]

@pytest.fixture
def service(tmp_path):
    source = JsonPropertyRepository(ROOT / 'backend/data/curated_demo_properties.json')
    rows = source.list_properties()
    for row in rows[:2]:
        source._records[row.property.property_id].property.provenance['customer_id'] = 'SHARED-OWNER'
    repo = EditableRepository(source, tmp_path/'memory.db')
    store = MemoryStore(repo.database_path)
    engines = BackendAdvisorEngines(lambda:repo, lambda:P4RetrofitAdapter(), lambda:P4CarbonAdapter(), lambda:ExistingValuationAdapter())
    return MemoryAdvisorService(engines, None, lambda:repo, store)

def chat(service, message, prop='DEMO-P00001'):
    return asyncio.run(service.chat(ChatRequest(property_id=prop, message=message)))

def update(service, **changes):
    customer, _ = identity(service.repository(), 'DEMO-P00001')
    old = service.store.load(customer)
    return service.store.update(customer, 'DEMO-P00001', MemoryUpdate(revision=old['revision'], **changes))

def test_persistence_identity_isolation_and_revision(service):
    update(service, preferences=Preferences(budget_gbp=1733, objective='energy_reduction'), completed_retrofits=['loft_insulation'])
    customer, _ = identity(service.repository(), 'DEMO-P00001')
    reopened = MemoryStore(service.store.path)
    assert reopened.load(customer)['preferences']['budget_gbp'] == 1733
    other, _ = identity(service.repository(), 'DEMO-P00002')
    assert customer == other
    assert 'DEMO-P00002' not in reopened.load(customer)['properties']
    assert reopened.load('different-owner')['preferences']['budget_gbp'] is None
    with pytest.raises(MemoryConflict):
        reopened.update(customer, 'DEMO-P00001', MemoryUpdate(revision=0, reset=True))
    edited = service.repository().load_property('DEMO-P00001')
    edited.property.provenance['customer_id'] = 'INJECTED-OWNER'
    service.repository().save_property(edited)
    assert identity(service.repository(),'DEMO-P00001')[0] == customer

def test_budget_exclusions_and_feedback_change_real_optimizer(service):
    update(service, preferences=Preferences(budget_gbp=1733, objective='energy_reduction'))
    before = chat(service, 'Use my saved preferences')
    assert before.status in ('success','partial')
    package = before.result['applied_retrofits']
    assert package
    assert before.result['installation_cost_gbp'] <= 1733
    update(service, feedback={'retrofits':package, 'response':'rejected'})
    after = chat(service, 'Use my saved preferences')
    assert after.result['applied_retrofits'] != package
    update(service, feedback={'retrofits':package, 'response':'accepted'})
    restored = chat(service, 'Use my saved preferences')
    assert restored.result['applied_retrofits'] == package
    assert restored.memory['completed_retrofits'] == []
    update(service, preferences=Preferences(budget_gbp=1733, objective='energy_reduction', excluded_retrofits=['loft_insulation']))
    excluded = chat(service,'Use my saved preferences')
    assert 'loft_insulation' not in excluded.result['applied_retrofits']
    assert any(d['status'] == 'excluded' for d in excluded.result['package_decisions'])

def test_completed_claim_requires_current_baseline_and_does_not_mutate_it(service):
    original = service.repository().load_property('DEMO-P00001').model_dump()
    update(service, preferences=Preferences(budget_gbp=5000), completed_retrofits=['loft_insulation'])
    result = chat(service,'Use my saved preferences')
    assert result.status == 'unavailable' and result.tool_calls == []
    assert 'Update' in result.explanation
    assert service.repository().load_property('DEMO-P00001').model_dump() == original
    other = chat(service,'Why is my score low?', 'DEMO-P00002')
    assert other.memory['completed_retrofits'] == []

def test_followup_survives_restart_recalculates_and_explicit_budget_wins(service):
    update(service, preferences=Preferences(budget_gbp=1733, objective='energy_reduction'))
    initial = chat(service,'Use my saved preferences')
    restarted = MemoryAdvisorService(service.engines, None, service.repository, MemoryStore(service.store.path))
    followup = chat(restarted,'what do you mean')
    assert followup.intent.intent == 'optimize_budget'
    assert followup.intent.budget_gbp == 1733
    assert 'optimize' in followup.tool_calls
    assert followup.result['applied_retrofits'] == initial.result['applied_retrofits']
    explicit = chat(restarted,'What can I do with a £200 budget?')
    assert explicit.intent.budget_gbp == 200
    assert explicit.result['installation_cost_gbp'] <= 200
    assert explicit.memory['preferences']['budget_gbp'] == 1733

def test_constraints_block_natural_language_simulation_and_history_is_bounded(service):
    update(service, preferences=Preferences(excluded_retrofits=['heat_pump']))
    result=chat(service,'What if I install a heat pump?')
    assert result.status == 'conditional'
    assert 'simulate' not in result.tool_calls
    assert 'saved' in result.explanation
    for _ in range(22): chat(service,'Why is my score low?')
    customer,_=identity(service.repository(),'DEMO-P00001')
    assert len(service.store.load(customer)['properties']['DEMO-P00001']['history']) == 20

def test_remember_budget_is_explicit_local_and_reset_restores_defaults(service):
    result=chat(service,'Remember my budget is £2,750')
    assert result.memory['preferences']['budget_gbp'] == 2750
    assert result.tool_calls == []
    assert chat(service,'Remember my budget is £1000000001').status == 'clarification_required'
    update(service,reset=True)
    customer,_=identity(service.repository(),'DEMO-P00001')
    assert service.store.load(customer)['preferences']['budget_gbp'] is None
    assert service.store.load(customer)['properties'] == {}

def test_memory_api_unknown_invalid_and_conflict(service, monkeypatch):
    from app.main import app
    monkeypatch.setattr(app.state,'advisor_service', service)
    c=TestClient(app)
    assert c.get('/advisor/memory/UNKNOWN').status_code==404
    path='/advisor/memory/DEMO-P00001'
    assert c.put(path,json={'revision':0,'preferences':{'budget_gbp':-1}}).status_code==422
    assert c.put(path,json={'revision':0,'preferences':{'budget_gbp':1733}}).status_code==200
    assert c.put(path,json={'revision':0,'reset':True}).status_code==409
    assert c.get(path).json()['preferences']['budget_gbp']==1733

def test_saved_budget_caps_implicit_scenario_and_completed_followup_cannot_use_old_baseline(service):
    update(service, preferences=Preferences(budget_gbp=1733, objective='energy_reduction'))
    simulated = chat(service,'What if I install a heat pump?')
    assert simulated.intent.budget_gbp == 1733
    assert simulated.status == 'unavailable'
    assert 'budget' in simulated.explanation.lower()
    chat(service,'Use my saved preferences')
    update(service,completed_retrofits=['loft_insulation'])
    followup = chat(service,'what do you mean')
    assert followup.status == 'unavailable' and followup.tool_calls == []

def test_updated_baseline_unblocks_completed_work_without_recommending_it_again(service):
    from app.services.orchestrator import run_scenario
    from app.schemas.models import ScenarioRequest
    record=service.repository().load_property('DEMO-P00001')
    payload=record.model_dump(exclude={'dataset_kind','dataset_source'})
    simulated=run_scenario(ScenarioRequest.model_validate({**payload,'retrofits':['loft_insulation']}), P4RetrofitAdapter(), P4CarbonAdapter(), ExistingValuationAdapter())
    assert simulated.updated_property is not None
    update(service, preferences=Preferences(budget_gbp=1733), completed_retrofits=['loft_insulation'])
    record.property=simulated.updated_property
    record.annual_energy.electricity_kwh=simulated.energy.after.electricity_kwh
    record.annual_energy.gas_kwh=simulated.energy.after.gas_kwh
    service.repository().save_property(record)
    result=chat(service,'Use my saved preferences')
    assert result.status in ('success','partial')
    assert 'loft_insulation' not in result.result['applied_retrofits']

def test_saved_action_uses_one_explanation_call_no_memory_extraction_calls(service):
    calls=[]
    class Provider:
        async def complete(self,system,payload):
            calls.append(payload)
            assert 'answer_facts' in payload
            fact=next(f for f in payload['answer_facts'] if f['source']=='optimization_context')
            return {'sentences':[{'text':'The selected package meets your remembered budget and priority within the supplied evidence.', 'fact_ids':[fact['id']]}]}
    service.provider=Provider()
    update(service,preferences=Preferences(budget_gbp=1733))
    result=chat(service,'Use my saved preferences')
    assert result.mode=='grounded_llm'
    assert len(calls)==1
    assert result.memory['used_revision'] < result.memory['revision']

def test_stale_baseline_blocks_model_extracted_scenario_without_generating_estimates(service):
    class Provider:
        async def complete(self,system,payload):
            assert 'question' in payload and 'answer_facts' not in payload
            return {'intent':'simulate_retrofit','retrofits':['solar_panels'],'budget_gbp':None,'objective':'carbon_reduction'}
    service.provider=Provider()
    update(service,completed_retrofits=['loft_insulation'])
    result=chat(service,'Explore solar panels')
    assert result.status=='unavailable' and result.result is None
    assert 'Update Assessment' in result.explanation

def test_planner_and_advisor_apply_same_memory(service, monkeypatch):
    from app.main import app, get_repository
    monkeypatch.setattr(app.state, 'advisor_service', service)
    app.dependency_overrides[get_repository] = service.repository
    import app.main as main
    monkeypatch.setattr(main, 'repository', service.repository())
    try:
        client = TestClient(app)
        record = service.repository().load_property('DEMO-P00001')
        payload = record.model_dump(mode='json', exclude={'dataset_kind','dataset_source'})
        update(service, preferences=Preferences(budget_gbp=1733, excluded_retrofits=['loft_insulation']))
        result = client.post('/retrofits/optimize', json={**payload, 'budget_gbp':1733})
        assert result.status_code == 200
        assert all('loft_insulation' not in row['applied_retrofits'] for row in result.json()['ranked_packages'])
        recommendations = client.post('/retrofits/recommend', json=payload)
        assert recommendations.status_code == 200
        assert not any(row['retrofit']=='loft_insulation' for row in recommendations.json()['recommendations'])
        assert client.post('/scenarios/simulate', json={**payload,'retrofits':['loft_insulation']}).status_code == 409
        update(service, completed_retrofits=['loft_insulation'])
        for path, extra in [('/retrofits/optimize', {'budget_gbp':1733}), ('/retrofits/recommend', {}), ('/scenarios/simulate', {'retrofits':['smart_thermostat']})]:
            assert client.post(path, json={**payload, **extra}).status_code == 409
    finally:
        app.dependency_overrides.pop(get_repository, None)
