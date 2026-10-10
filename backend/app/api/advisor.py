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
