from fastapi import APIRouter, Request

from app.schemas import (
    ToolExecuteRequest,
    ToolExecuteResponse,
    ToolPlanRequest,
    ToolPlanResponse,
    Meta,
)
from app.core.errors import AppError
from app.services.llm_service import LLMService
from app.services.tool_service import ToolService


router = APIRouter(prefix="/tools", tags=["tools"])


def get_tool_service(request: Request) -> ToolService:
    service = getattr(request.app.state, "tool_service", None)
    if service is None:
        service = ToolService()
        request.app.state.tool_service = service
    return service


def get_llm_service(request: Request) -> LLMService:
    service = getattr(request.app.state, "llm_service", None)
    if service is None:
        service = LLMService()
        request.app.state.llm_service = service
    return service


@router.post(
    "/plan",
    response_model=ToolPlanResponse,
    summary="Plan a tool call",
    description="Sends user input to the LLM with available tool definitions and returns the selected tool plan for user approval.",
)
async def plan_tool(
    payload: ToolPlanRequest,
    request: Request,
) -> ToolPlanResponse:
    tool_service = get_tool_service(request)
    llm_service = get_llm_service(request)

    tool_defs = tool_service.get_openai_tool_definitions()
    result = await llm_service.plan_tool(payload.input, tool_defs)

    tool_name = result["tool_name"]
    definition = tool_service.tools.get(tool_name)
    if definition is None:
        raise AppError(
            "TOOL_NOT_ALLOWED",
            f"Tool '{tool_name}' is not allowed.",
            403,
            {"tool_name": tool_name},
        )

    return ToolPlanResponse(
        tool_name=tool_name,
        arguments=result["arguments"],
        requires_approval=definition.side_effect,
        meta=Meta(),
    )


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
