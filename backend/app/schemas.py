from typing import Any, Literal

from pydantic import BaseModel, Field


class ErrorDetails(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetails


class Meta(BaseModel):
    model: str | None = None
    latency_ms: int | None = None


class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=10_000)
    language: Literal["ru", "en"] = "ru"


class AnalyzeResponse(BaseModel):
    topics: list[str]
    pain_points: list[str]
    risks: list[str]
    next_questions: list[str]
    meta: Meta


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(..., min_length=1, max_length=8_000)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4_000)
    conversation_id: str | None = None
    history: list[ChatMessage] = Field(default_factory=list, max_length=20)


class ChatResponse(BaseModel):
    message: ChatMessage
    conversation_id: str | None = None
    meta: Meta


class ToolExecuteRequest(BaseModel):
    tool_name: str = Field(..., min_length=1)
    arguments: dict[str, Any] = Field(default_factory=dict)
    approved: bool = False


class ToolExecuteResponse(BaseModel):
    tool_name: str
    status: Literal["success"]
    result: dict[str, Any]
    meta: Meta


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    version: str
