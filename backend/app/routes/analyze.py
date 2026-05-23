from fastapi import APIRouter, Request

from app.schemas import AnalyzeRequest, AnalyzeResponse
from app.services.llm_service import LLMService


router = APIRouter(tags=["analyze"])


def get_llm_service(request: Request) -> LLMService:
    service = getattr(request.app.state, "llm_service", None)
    if service is None:
        service = LLMService()
        request.app.state.llm_service = service
    return service


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Analyze text",
    description="Returns structured topics, pain points, risks, and next questions.",
)
async def analyze_text(
    payload: AnalyzeRequest,
    request: Request,
) -> AnalyzeResponse:
    service = get_llm_service(request)
    return await service.analyze_text(payload.text, payload.language)
