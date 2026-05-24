from datetime import datetime
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


class FormAssistantRequest(BaseModel):
    context: str = Field(..., min_length=10, max_length=10_000)


class FormAssistantResponse(BaseModel):
    project_name: str
    target_user: str
    problem: str
    proposed_solution: str
    main_risks: list[str]
    success_metric: str
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


class ToolPlanRequest(BaseModel):
    input: str = Field(..., min_length=1, max_length=10_000)


class ToolPlanResponse(BaseModel):
    tool_name: str
    arguments: dict[str, Any]
    requires_approval: bool
    status: Literal["planned"] = "planned"
    meta: Meta


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    version: str


# --- Document QA ---

class SourceCreate(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255)
    content_type: Literal["text/plain", "text/markdown", "application/pdf"]
    content: str = Field(..., min_length=1, max_length=500_000)


class SourceOut(BaseModel):
    id: str
    filename: str
    content_type: str
    chunk_count: int
    created_at: datetime


class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4_000)
    source_ids: list[str] | None = None
    top_k: int = Field(default=5, ge=1, le=20)


class CitationOut(BaseModel):
    source_id: str
    source_filename: str
    chunk_position: int
    chunk_text: str


class FailureCaseOut(BaseModel):
    question: str
    expected_answer: str
    actual_answer: str
    retrieval_issue: str


class QuestionResponse(BaseModel):
    question: str
    answer: str
    citations: list[CitationOut]
    latency_ms: int
    failure_case: FailureCaseOut | None = None
