from fastapi import APIRouter, Request

from app.routes.analyze import get_llm_service
from app.schemas import ChatRequest, ChatResponse


router = APIRouter(tags=["chat"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Chat with assistant",
    description="Returns a non-streaming assistant response for the provided message.",
)
async def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    service = get_llm_service(request)
    return await service.chat(
        message=payload.message,
        history=payload.history,
        conversation_id=payload.conversation_id,
    )
