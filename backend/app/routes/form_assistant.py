from fastapi import APIRouter, Request

from app.routes.analyze import get_llm_service
from app.schemas import FormAssistantRequest, FormAssistantResponse


router = APIRouter(tags=["form-assistant"])


@router.post(
    "/form-assistant",
    response_model=FormAssistantResponse,
    summary="Suggest form values",
    description="Returns structured project form suggestions for approval.",
)
async def suggest_form_values(
    payload: FormAssistantRequest,
    request: Request,
) -> FormAssistantResponse:
    service = get_llm_service(request)
    return await service.suggest_form_values(payload.context)
