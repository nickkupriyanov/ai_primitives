from fastapi import APIRouter, Request

from app.schemas import ToolExecuteRequest, ToolExecuteResponse
from app.services.tool_service import ToolService


router = APIRouter(prefix="/tools", tags=["tools"])


def get_tool_service(request: Request) -> ToolService:
    service = getattr(request.app.state, "tool_service", None)
    if service is None:
        service = ToolService()
        request.app.state.tool_service = service
    return service


@router.post(
    "/execute",
    response_model=ToolExecuteResponse,
    summary="Execute an allowed tool",
    description="Executes whitelisted backend tools and requires approval for side effects.",
)
async def execute_tool(
    payload: ToolExecuteRequest,
    request: Request,
) -> ToolExecuteResponse:
    service = get_tool_service(request)
    return await service.execute_tool(
        tool_name=payload.tool_name,
        arguments=payload.arguments,
        approved=payload.approved,
    )
