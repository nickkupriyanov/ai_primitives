import re
import time
from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from app.core.errors import AppError
from app.schemas import Meta, ToolExecuteResponse


class TextArgs(BaseModel):
    text: str = Field(..., min_length=1, max_length=10_000)


class SaveNoteArgs(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=10_000)


ToolHandler = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


class ToolDefinition(BaseModel):
    side_effect: bool
    handler_name: str


class ToolService:
    def __init__(self) -> None:
        self.tools: dict[str, ToolDefinition] = {
            "summarize_text": ToolDefinition(
                side_effect=False, handler_name="_summarize_text"
            ),
            "classify_priority": ToolDefinition(
                side_effect=False, handler_name="_classify_priority"
            ),
            "extract_action_items": ToolDefinition(
                side_effect=False, handler_name="_extract_action_items"
            ),
            "save_note": ToolDefinition(side_effect=True, handler_name="_save_note"),
        }

    def get_openai_tool_definitions(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "summarize_text",
                    "description": "Summarize a piece of text into a shorter version.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "The text to summarize",
                            }
                        },
                        "required": ["text"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "classify_priority",
                    "description": "Classify the priority level of a given text or task description.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "The text to classify",
                            }
                        },
                        "required": ["text"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "extract_action_items",
                    "description": "Extract action items and todos from a given text.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "The text to extract action items from",
                            }
                        },
                        "required": ["text"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "save_note",
                    "description": "Save a note with a title and content. Requires user approval.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "The note title",
                            },
                            "content": {
                                "type": "string",
                                "description": "The note content",
                            },
                        },
                        "required": ["title", "content"],
                    },
                },
            },
        ]

    async def execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        approved: bool,
    ) -> ToolExecuteResponse:
        started = time.perf_counter()
        definition = self.tools.get(tool_name)
        if definition is None:
            raise AppError(
                "TOOL_NOT_ALLOWED",
                f"Tool '{tool_name}' is not allowed.",
                403,
                {"tool_name": tool_name},
            )

        if definition.side_effect and not approved:
            raise AppError(
                "APPROVAL_REQUIRED",
                f"Tool '{tool_name}' requires approved=true before execution.",
                403,
                {"tool_name": tool_name},
            )

        try:
            handler = getattr(self, definition.handler_name)
            result = await handler(arguments)
        except ValidationError as exc:
            raise AppError(
                "VALIDATION_ERROR",
                "Invalid tool arguments.",
                422,
                {"errors": exc.errors()},
            ) from exc
        except AppError:
            raise
        except Exception as exc:
            raise AppError(
                "TOOL_EXECUTION_ERROR",
                "Tool execution failed.",
                500,
                {"tool_name": tool_name, "type": exc.__class__.__name__},
            ) from exc

        latency_ms = int((time.perf_counter() - started) * 1000)
        return ToolExecuteResponse(
            tool_name=tool_name,
            status="success",
            result=result,
            meta=Meta(latency_ms=latency_ms),
        )

    async def _summarize_text(self, arguments: dict[str, Any]) -> dict[str, Any]:
        args = TextArgs.model_validate(arguments)
        summary = args.text.strip()
        if len(summary) > 160:
            summary = summary[:157].rstrip() + "..."
        return {"summary": summary}

    async def _classify_priority(self, arguments: dict[str, Any]) -> dict[str, Any]:
        args = TextArgs.model_validate(arguments)
        text = args.text.lower()
        if any(word in text for word in ("urgent", "critical", "blocked", "asap")):
            priority = "high"
        elif len(text) > 100 or any(word in text for word in ("soon", "important")):
            priority = "medium"
        else:
            priority = "low"
        return {"priority": priority, "reason": "Based on urgency keywords and length."}

    async def _extract_action_items(self, arguments: dict[str, Any]) -> dict[str, Any]:
        args = TextArgs.model_validate(arguments)
        sentences = re.split(r"(?<=[.!?])\s+", args.text.strip())
        action_items = [
            sentence.strip("- ")
            for sentence in sentences
            if re.search(r"\b(need|should|must|todo|action|fix|add|create)\b", sentence, re.I)
        ]
        return {"action_items": action_items[:10]}

    async def _save_note(self, arguments: dict[str, Any]) -> dict[str, Any]:
        args = SaveNoteArgs.model_validate(arguments)
        return {
            "saved": True,
            "note": {"title": args.title, "content": args.content},
        }
