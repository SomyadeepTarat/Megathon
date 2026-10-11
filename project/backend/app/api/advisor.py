"""Person 1: include router and set app.state.advisor_service at startup."""
from fastapi import APIRouter, HTTPException, Request

from ..services.llm_service import ChatRequest, ChatResponse, PropertyNotFound

router = APIRouter(prefix='/advisor', tags=['advisor'])


@router.post('/chat', response_model=ChatResponse)
async def chat(body: ChatRequest, request: Request) -> ChatResponse:
    service = getattr(request.app.state, 'advisor_service', None)
    if service is None:
        raise HTTPException(503, 'Advisor engine adapters have not been connected')
    try:
        return await service.chat(body)
    except PropertyNotFound:
        raise HTTPException(404, 'Property not found') from None


@router.post('/chat/stream')
async def chat_stream(body: ChatRequest, request: Request):
    """Stream real tool progress; publish the answer only after grounding validation."""
    import asyncio
    import json
    from fastapi.responses import StreamingResponse
    service = getattr(request.app.state, 'advisor_service', None)
    if service is None:
        raise HTTPException(503, 'Advisor engine adapters have not been connected')

    async def events():
        queue = asyncio.Queue()
        async def progress(message):
            await queue.put(('progress', {'message': message}))
        async def execute():
            try:
                result = await service.chat(body, progress=progress)
                await queue.put(('result', result.model_dump(mode='json')))
            except PropertyNotFound:
                await queue.put(('error', {'message': 'Property not found'}))
            except Exception:
                await queue.put(('error', {'message': 'The advisor could not complete this request. Please retry.'}))
        task = asyncio.create_task(execute())
        try:
            while True:
                try:
                    event, data = await asyncio.wait_for(queue.get(), timeout=5)
                except asyncio.TimeoutError:
                    yield ': keep-alive\n\n'
                    continue
                yield f'event: {event}\ndata: {json.dumps(data)}\n\n'
                if event in ('result', 'error'):
                    break
        finally:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
    return StreamingResponse(events(), media_type='text/event-stream',
                             headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


from ..services.customer_memory import MemoryUpdate, MemoryConflict, identity, view

@router.get('/memory/{property_id}')
async def read_memory(property_id: str, request: Request):
    service = request.app.state.advisor_service
    try:
        customer, _ = identity(service.repository(), property_id)
    except PropertyNotFound:
        raise HTTPException(404, 'Property not found') from None
    return view(service.store.load(customer), property_id)

@router.put('/memory/{property_id}')
async def update_memory(property_id: str, body: MemoryUpdate, request: Request):
    service = request.app.state.advisor_service
    try:
        customer, _ = identity(service.repository(), property_id)
        return view(service.store.update(customer, property_id, body), property_id)
    except PropertyNotFound:
        raise HTTPException(404, 'Property not found') from None
    except MemoryConflict:
        raise HTTPException(409, 'Memory changed in another request. Reload your saved preferences and try again.') from None
