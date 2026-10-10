import logging
import os
from pathlib import Path
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.efficiency import assess
from app.db.repository import JsonPropertyRepository
from app.schemas.models import AssessmentRequest, AssessmentResponse, ScenarioRequest
from app.schemas.engines import PropertyRecord, PropertySummary, ScenarioResponse
from app.services.adapters import PendingRetrofitEngine, PendingCarbonEngine, ExistingValuationAdapter
from app.services.orchestrator import EngineContractError, run_scenario

app = FastAPI(title='GreenPrint AI', version='0.2.0')
app.add_middleware(CORSMiddleware,
    allow_origins=[x.strip() for x in os.getenv('GREENPRINT_CORS_ORIGINS', 'http://localhost:3000').split(',') if x.strip()],
    allow_methods=['GET', 'POST'], allow_headers=['Content-Type'], allow_credentials=False)
repository = JsonPropertyRepository(Path(__file__).resolve().parents[1] / 'data/demo_properties.json')


def get_repository():
    return repository


def get_retrofit_engine():
    return PendingRetrofitEngine()


def get_carbon_engine():
    return PendingCarbonEngine()


def get_valuation_engine():
    return ExistingValuationAdapter()


@app.exception_handler(EngineContractError)
async def engine_contract_error(request, exc):
    logging.getLogger(__name__).error('Engine contract failed: %s', exc)
    return JSONResponse(status_code=500, content={'status': 'error', 'reason': 'An engine returned inconsistent results.'})


@app.get('/health')
def health():
    return {'status': 'ok', 'version': '0.2.0',
            'capabilities': {'scoring': True, 'property_repository': 'synthetic_development_fixtures',
                             'retrofit_simulation': False, 'valuation': 'adapter_present', 'advisor': False}}


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


@app.post('/scenarios/simulate', response_model=ScenarioResponse,
          responses={409: {'model': ScenarioResponse}, 503: {'model': ScenarioResponse}})
def simulate(request: ScenarioRequest, retrofit=Depends(get_retrofit_engine),
             carbon=Depends(get_carbon_engine), valuation=Depends(get_valuation_engine)):
    result = run_scenario(request, retrofit, carbon, valuation)
    status_code = {'rejected': 409, 'unavailable': 503}.get(result.status, 200)
    return JSONResponse(status_code=status_code, content=result.model_dump(mode='json'))
