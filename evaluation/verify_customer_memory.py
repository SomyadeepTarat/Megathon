"""Verify persistent memory offline; --live-api makes exactly one primary API call.
No burst testing, retries, intent extraction or live fallback calls.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live-api', action='store_true')
    args=parser.parse_args()
    output=ROOT/'evaluation/results/customer_memory';output.mkdir(parents=True,exist_ok=True)
    report={'scope':'Explicit synthetic curated test fixture; no measured savings or human quality claims','live_primary_calls':0}
    from app.core.environment import load_project_environment
    load_project_environment()
    if args.live_api:
        stamp=output/'last_live_call.json'
        if stamp.exists() and time.time()-json.loads(stamp.read_text())['epoch']<60:
            raise SystemExit('No call made: wait at least 60 seconds between live checks.')
    from app.services.llm_service import GroqProvider, FallbackProvider, provider_from_env, ChatRequest
    from app.services.customer_memory import MemoryStore, MemoryAdvisorService, MemoryUpdate, Preferences, identity
    from app.services.advisor_adapter import BackendAdvisorEngines
    from app.db.repository import JsonPropertyRepository, EditableRepository
    from app.services.p4_adapter import P4RetrofitAdapter, P4CarbonAdapter
    from app.services.adapters import ExistingValuationAdapter
    import asyncio
    with tempfile.TemporaryDirectory(prefix='memory-evaluation-') as temporary:
        source=JsonPropertyRepository(ROOT/'backend/data/curated_demo_properties.json')
        repository=EditableRepository(source,Path(temporary)/'properties.db')
        store=MemoryStore(repository.database_path)
        engines=BackendAdvisorEngines(lambda:repository,lambda:P4RetrofitAdapter(),lambda:P4CarbonAdapter(),lambda:ExistingValuationAdapter())
        service=MemoryAdvisorService(engines,None,lambda:repository,store)
        customer,_=identity(repository,'DEMO-P00001')
        store.update(customer,'DEMO-P00001',MemoryUpdate(revision=0,preferences=Preferences(budget_gbp=1733,objective='energy_reduction')))
        def run():return asyncio.run(service.chat(ChatRequest(property_id='DEMO-P00001',message='Use my saved preferences')))
        before=run();assert before.status in ('success','partial')
        package=before.result['applied_retrofits'];assert package
        service.store=MemoryStore(repository.database_path)
        value=service.store.load(customer)
        service.store.update(customer,'DEMO-P00001',MemoryUpdate(revision=value['revision'],feedback={'retrofits':package,'response':'rejected'}))
        after=run();assert after.result['applied_retrofits']!=package
        report.update(persistence='passed',adaptation='passed',before=before.model_dump(mode='json'),after=after.model_dump(mode='json'))
        if args.live_api:
            p=provider_from_env();p=p.primary if isinstance(p,FallbackProvider) else p
            if not isinstance(p,GroqProvider):raise SystemExit('Configure Groq for the single live primary test')
            class SingleCall:
                async def complete(self,system,payload):
                    assert 'answer_facts' in payload, 'No live intent or memory extraction calls permitted'
                    assert report['live_primary_calls']==0, 'Refusing another live call'
                    report['live_primary_calls']+=1
                    stamp.write_text(json.dumps({'epoch':time.time()})+'\n')
                    try:
                        answer=await p.complete(system,payload)
                        report['primary_transport']='passed'
                        return answer
                    except Exception as exc:
                        report.update(primary_transport='failed',error_type=type(exc).__name__,http_status=getattr(exc,'code',None))
                        raise
            service.provider=SingleCall()
            response=run()
            report.update(model=p.model,live_answer=response.model_dump(mode='json'),live_grounding=response.mode)
            report['status']='passed' if report.get('primary_transport')=='passed' and response.mode=='grounded_llm' else 'live_check_failed_no_retry'
        else: report['status']='passed_offline'
    path=output/('live.json' if args.live_api else 'offline.json')
    path.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report.get(k)for k in ('status','persistence','adaptation','live_primary_calls','primary_transport','live_grounding','model','http_status')},indent=2))
    if report['status']=='live_check_failed_no_retry':raise SystemExit(1)

if __name__=='__main__':main()
