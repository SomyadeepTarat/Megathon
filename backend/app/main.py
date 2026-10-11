from app.services.valuation_inputs import impact_input_reason
import logging
import os
from pathlib import Path
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.efficiency import assess
from app.db.repository import JsonPropertyRepository, CsvPropertyRepository, EditableRepository
from app.schemas.models import AssessmentRequest, AssessmentResponse, ScenarioRequest, RecommendationRequest, OptimizationRequest
from app.schemas.engines import PropertyRecord, PropertySummary, ScenarioResponse, RecommendationResponse, OptimizationResult, ValuationRequest, ValuationResult, FullAssessmentResponse, EnergyImpact, FuelState
from app.services.adapters import ExistingValuationAdapter
from app.services.p4_adapter import P4RetrofitAdapter, P4CarbonAdapter, configured_factors
from app.services.recommendations import recommend
from app.services.optimization import optimize_packages
from app.services.orchestrator import EngineContractError, run_scenario
from app.api.advisor import router as advisor_router
from app.services.advisor_adapter import BackendAdvisorEngines
from app.services.llm_service import AdvisorService, provider_from_env
from app.schemas.valuation import BaselineValuationResponse
from app.schemas.engines import HealthResponse, PortfolioEntry
from app.services.portfolio import rank_portfolio

app = FastAPI(title='GreenPrint AI', version='0.3.0')
app.add_middleware(CORSMiddleware,
    allow_origins=[x.strip() for x in os.getenv('GREENPRINT_CORS_ORIGINS', 'http://localhost:3000').split(',') if x.strip()],
    allow_methods=['GET', 'POST'], allow_headers=['Content-Type'], allow_credentials=False)
project_root = Path(__file__).resolve().parents[2]
dataset_kind = os.getenv('GREENPRINT_PROPERTY_DATASET', 'csv')
if dataset_kind == 'csv':
    repository = CsvPropertyRepository.from_project_root(project_root)
elif dataset_kind == 'demo':
    repository = JsonPropertyRepository(project_root / 'backend/data/curated_demo_properties.json')
elif dataset_kind == 'fixtures':
    repository = JsonPropertyRepository(project_root / 'backend/data/demo_properties.json')
else:
    raise ValueError('GREENPRINT_PROPERTY_DATASET must be csv, demo or fixtures')


repository = EditableRepository(repository, os.getenv('GREENPRINT_DB_PATH', str(project_root / 'backend/data/user_properties.db')))


def get_repository():
    return repository


def get_retrofit_engine():
    return P4RetrofitAdapter()


def get_carbon_engine():
    return P4CarbonAdapter()


def get_valuation_engine():
    return ExistingValuationAdapter()


@app.exception_handler(EngineContractError)
async def engine_contract_error(request, exc):
    logging.getLogger(__name__).error('Engine contract failed: %s', exc)
    return JSONResponse(status_code=500, content={'status': 'error', 'reason': 'An engine returned inconsistent results.'})


@app.get('/health', response_model=HealthResponse)
def health():
    try:
        factors = configured_factors()
        factor_ready = {'ready': factors is not None, 'reason': None if factors else 'Set GREENPRINT_EMISSION_FACTORS_FILE or supply factors in requests.'}
    except (ValueError, OSError) as exc:
        factor_ready = {'ready': False, 'reason': f'Configured factors cannot be loaded: {type(exc).__name__}'}
    model_ready = Path(os.getenv('VALUATION_MODEL_PATH', project_root / 'ml/models/valuation.joblib')).is_file()
    return {'status': 'ok', 'version': '0.3.0',
            'capabilities': {'scoring': True, 'property_repository': dataset_kind,
                             'retrofit_simulation': 'connected_input_dependent', 'valuation': 'adapter_present', 'advisor': True},
            'readiness': {'retrofit_engine': {'connected': True, 'requires': ['confirmed feasibility', 'physical inputs', 'documented factors']},
                          'emissions_factors': factor_ready,
                          'valuation': {'artifact_present': model_ready, 'synthetic_impact_artifact_present': (project_root / 'ml/models/synthetic_impact.joblib').is_file(), 'evidence_supported': 'checked per request; illustrative intensity-based impact only for explicitly synthetic property and energy inputs'},
                          'advisor': {'mounted': True, 'provider': os.getenv('LLM_PROVIDER', 'deterministic')},
                          'scoring': {'complete_dataset_scores_ready': all(assess(row).score.status == 'available' for row in repository.list_properties()), 'requires': ['applicable benchmark and complete component inputs']},
                          'budget_optimizer': {'ready': True, 'requires': ['budget', 'documented costs for selected measures', 'objective-specific inputs']}}}


@app.get('/properties', response_model=list[PropertySummary])
def properties(repo=Depends(get_repository)):
    return [PropertySummary(property_id=row.property.property_id, property_type=row.property.property_type,
                            region=row.property.region, dataset_kind=row.dataset_kind,
                            dataset_source=row.dataset_source) for row in repo.list_properties()]


def load_record(repo, property_id):
    try:
        return repo.load_property(property_id)
    except KeyError:
        raise HTTPException(status_code=404, detail='Property not found') from None


@app.get('/properties/ranking', response_model=list[PortfolioEntry])
@app.get('/portfolio/rank', response_model=list[PortfolioEntry])
def portfolio(repo=Depends(get_repository), retrofit=Depends(get_retrofit_engine),
              carbon=Depends(get_carbon_engine), valuation=Depends(get_valuation_engine)):
    return rank_portfolio(repo, retrofit, carbon, valuation)


@app.get('/properties/{property_id}', response_model=PropertyRecord)
def property_details(property_id: str, repo=Depends(get_repository)):
    return load_record(repo, property_id)


@app.get('/properties/{property_id}/assessment', response_model=AssessmentResponse)
def property_assessment(property_id: str, repo=Depends(get_repository)):
    row = load_record(repo, property_id)
    return assess(AssessmentRequest(property=row.property, annual_energy=row.annual_energy, benchmark=row.benchmark))


@app.post('/assessments', response_model=AssessmentResponse)
def assessment(request: AssessmentRequest):
    return assess(request)


@app.get('/properties/{property_id}/valuation', response_model=BaselineValuationResponse)
@app.post('/properties/{property_id}/valuation', response_model=BaselineValuationResponse)
def baseline_valuation(property_id: str, repo=Depends(get_repository)):
    record = load_record(repo, property_id)
    try:
        from app.services.valuation_service import predict_property_value
    except ImportError:
        result = {'status': 'unavailable', 'reason': 'Install the ML dependencies to enable baseline valuation'}
    else:
        result = predict_property_value(record.property, allow_illustrative=record.dataset_kind == 'synthetic')
    return {'property_id': property_id, **result}


@app.post('/scenarios/simulate', response_model=ScenarioResponse,
          responses={409: {'model': ScenarioResponse}, 503: {'model': ScenarioResponse}})
def simulate(request: ScenarioRequest, retrofit=Depends(get_retrofit_engine),
             carbon=Depends(get_carbon_engine), valuation=Depends(get_valuation_engine)):
    result = run_scenario(request, retrofit, P4CarbonAdapter(request.emission_factors) if isinstance(carbon, P4CarbonAdapter) else carbon, valuation)
    status_code = {'rejected': 409, 'unavailable': 503}.get(result.status, 200)
    return JSONResponse(status_code=status_code, content=result.model_dump(mode='json'))


@app.post('/assessments/full', response_model=FullAssessmentResponse)
def full_assessment(request: AssessmentRequest, engine=Depends(get_valuation_engine)):
    return FullAssessmentResponse(property_id=request.property.property_id, assessment=assess(request),
        annual_energy=request.annual_energy, baseline_carbon=P4CarbonAdapter(request.emission_factors).baseline(request),
        valuation=engine.predict_value_impact(request.property, request.property))


@app.post('/properties', response_model=PropertyRecord, status_code=201)
def register_property(request: AssessmentRequest, repo=Depends(get_repository)):
    declared = request.property.provenance.get('record')
    kind = declared if declared in ('synthetic', 'observed', 'estimated', 'imported') else 'synthetic' if request.annual_energy.quality == 'synthetic' else 'imported'
    return repo.save_property(PropertyRecord(**request.model_dump(), dataset_kind=kind,
        dataset_source='User-supplied API snapshot; persisted in the local SQLite repository.'))


@app.post('/retrofits/recommend', response_model=RecommendationResponse)
def recommendations(request: RecommendationRequest, retrofit=Depends(get_retrofit_engine),
                    carbon=Depends(get_carbon_engine), valuation=Depends(get_valuation_engine), repo=Depends(get_repository)):
    result = recommend(request, retrofit, P4CarbonAdapter(request.emission_factors) if isinstance(carbon, P4CarbonAdapter) else carbon, valuation)
    return repo.save_recommendations(request, result)


@app.get('/properties/{property_id}/recommendations', response_model=RecommendationResponse)
def stored_recommendations(property_id: str, scenario_id: str | None = None, repo=Depends(get_repository)):
    try:
        return repo.load_recommendations(property_id, scenario_id)
    except KeyError:
        raise HTTPException(status_code=404, detail='No stored recommendations for this property/scenario') from None


@app.post('/retrofits/optimize', response_model=OptimizationResult)
def optimize(request: OptimizationRequest, retrofit=Depends(get_retrofit_engine),
             carbon=Depends(get_carbon_engine), valuation=Depends(get_valuation_engine)):
    return optimize_packages(request, retrofit,
        P4CarbonAdapter(request.emission_factors) if isinstance(carbon, P4CarbonAdapter) else carbon,
        valuation)


@app.post('/properties/{property_id}/valuation/impact', response_model=ValuationResult)
def valuation(property_id: str, request: ValuationRequest, repo=Depends(get_repository), engine=Depends(get_valuation_engine)):
    record = load_record(repo, property_id)
    baseline = record.property
    scenario = request.scenario_property or baseline
    from app.services.input_consistency import conflicting_inputs
    conflicts = sorted(set(conflicting_inputs(baseline) + conflicting_inputs(scenario)))
    if conflicts:
        return ValuationResult(status='unavailable', reason='Conflicting property evidence: ' + '; '.join(conflicts) + '. Confirm these inputs before estimating value impact.')
    if scenario.property_id != property_id:
        raise HTTPException(422, 'Scenario property ID differs from baseline')
    input_reason = impact_input_reason(baseline, scenario)
    if input_reason:
        return ValuationResult(status='unavailable', reason=input_reason)
    if request.scenario_annual_energy is not None:
        before, after = record.annual_energy, request.scenario_annual_energy
        if after.quality not in ('synthetic', 'estimated'):
            return ValuationResult(status='unavailable', reason='Scenario energy must be explicitly synthetic or estimated for illustrative impact; observed after data needs separate validation.')
        if any(value is None for value in [before.electricity_kwh, before.gas_kwh, after.electricity_kwh, after.gas_kwh]):
            return ValuationResult(status='unavailable', reason='Both baseline and scenario fuel totals are required for energy-based value impact.')
        e, g = before.electricity_kwh-after.electricity_kwh, before.gas_kwh-after.gas_kwh
        total = before.electricity_kwh+before.gas_kwh
        energy = EnergyImpact(baseline=FuelState(electricity_kwh=before.electricity_kwh, gas_kwh=before.gas_kwh),
            after=FuelState(electricity_kwh=after.electricity_kwh, gas_kwh=after.gas_kwh),
            electricity_savings_kwh=e, gas_savings_kwh=g, net_savings_kwh=e+g,
            improvement_percentage=100*(e+g)/total if total else None)
        if hasattr(engine, 'predict_scenario_impact'):
            return engine.predict_scenario_impact(record, scenario, energy)
        return ValuationResult(status='unavailable', reason='The configured valuation engine does not support energy-based scenario impact.')
    if scenario.model_dump() != baseline.model_dump():
        return ValuationResult(status='unavailable', reason='No supported projected EPC estimate for the retrofit scenario.')
    return engine.predict_value_impact(baseline, scenario)


app.include_router(advisor_router)
app.state.advisor_service = AdvisorService(
    BackendAdvisorEngines(lambda: get_repository(), lambda: get_retrofit_engine(),
                         lambda: get_carbon_engine(), lambda: get_valuation_engine()),
    provider=provider_from_env(),
)
