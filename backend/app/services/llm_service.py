import asyncio
import json
import time
from typing import Any

from app.config import Settings, get_settings
from app.core.errors import AppError
from app.observability.logging import get_logger
from app.schemas import (
    AnalyzeResponse,
    ChatMessage,
    ChatResponse,
    FormAssistantResponse,
    Meta,
)


logger = get_logger(__name__)


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        return [value]
    return []


class LLMService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._client: Any | None = None

    def _get_client(self) -> Any:
        if not self.settings.openai_api_key:
            raise AppError(
                "LLM_PROVIDER_ERROR",
                "Missing OPENAI_API_KEY or AI_API_KEY environment variable.",
                502,
            )

        if self._client is None:
            try:
                from openai import AsyncOpenAI
            except ImportError as exc:
                raise AppError(
                    "LLM_PROVIDER_ERROR",
                    "OpenAI SDK is not installed.",
                    502,
                ) from exc

            kwargs: dict[str, Any] = {"api_key": self.settings.openai_api_key}
            if self.settings.openai_base_url:
                kwargs["base_url"] = self.settings.openai_base_url
            self._client = AsyncOpenAI(**kwargs)
        return self._client

    async def analyze_text(self, text: str, language: str) -> AnalyzeResponse:
        started = time.perf_counter()
        raw = await self._complete_json(
            use_case="analyze",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an AI product analyst. Analyze the user's text "
                        "and return only JSON with topics, pain_points, risks, "
                        "and next_questions. Be concise and practical."
                        "Отвечай на русском"
                    ),
                },
                {"role": "user", "content": f"Language: {language}\n\nText:\n{text}"},
            ],
        )
        latency_ms = int((time.perf_counter() - started) * 1000)
        return AnalyzeResponse(
            topics=_string_list(raw.get("topics", [])),
            pain_points=_string_list(raw.get("pain_points", [])),
            risks=_string_list(raw.get("risks", [])),
            next_questions=_string_list(raw.get("next_questions", [])),
            meta=Meta(model=self.settings.openai_model, latency_ms=latency_ms),
        )

    async def chat(
        self,
        message: str,
        history: list[ChatMessage],
        conversation_id: str | None = None,
    ) -> ChatResponse:
        started = time.perf_counter()
        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": (
                    "You are a helpful AI backend assistant. Answer clearly, "
                    "practically, and concisely."
                ),
            }
        ]
        messages.extend(item.model_dump() for item in history)
        messages.append({"role": "user", "content": message})

        content = await self._complete_text("chat", messages)
        latency_ms = int((time.perf_counter() - started) * 1000)
        return ChatResponse(
            message=ChatMessage(role="assistant", content=content),
            conversation_id=conversation_id,
            meta=Meta(model=self.settings.openai_model, latency_ms=latency_ms),
        )

    async def suggest_form_values(self, context: str) -> FormAssistantResponse:
        started = time.perf_counter()
        raw = await self._complete_json(
            use_case="form_assistant",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a product strategist. The user describes a project. "
                        "Return only JSON with project_name, target_user, problem, "
                        "proposed_solution, main_risks, and success_metric. Keep values "
                        "concise and practical."
                    ),
                },
                {"role": "user", "content": context},
            ],
        )
        latency_ms = int((time.perf_counter() - started) * 1000)
        return FormAssistantResponse(
            project_name=str(raw.get("project_name", "")),
            target_user=str(raw.get("target_user", "")),
            problem=str(raw.get("problem", "")),
            proposed_solution=str(raw.get("proposed_solution", "")),
            main_risks=_string_list(raw.get("main_risks", [])),
            success_metric=str(raw.get("success_metric", "")),
            meta=Meta(model=self.settings.openai_model, latency_ms=latency_ms),
        )

    async def _complete_json(
        self, use_case: str, messages: list[dict[str, str]]
    ) -> dict[str, Any]:
        content = await self._complete_text(
            use_case,
            messages,
            response_format={"type": "json_object"},
        )
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise AppError(
                "LLM_PROVIDER_ERROR",
                "LLM returned invalid JSON.",
                502,
            ) from exc
        if not isinstance(parsed, dict):
            raise AppError("LLM_PROVIDER_ERROR", "LLM returned non-object JSON.", 502)
        return parsed

    async def plan_tool(
        self,
        user_input: str,
        tools: list[dict[str, Any]],
    ) -> dict[str, Any]:
        SYSTEM_PROMPT = (
            "You are a helpful assistant. Based on the user's input, decide which "
            "tool to call. You must use the provided tools. Do not respond with "
            "free-form text unless no tool is appropriate."
        )
        messages: list[dict[str, str]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ]

        response = await self._call_chat_completion(
            "tool_plan",
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        message = response.choices[0].message
        tool_calls = getattr(message, "tool_calls", None)

        if not tool_calls:
            raise AppError(
                "NO_TOOL_SELECTED",
                "The model did not select a tool. Try a more specific prompt.",
                422,
            )

        call = tool_calls[0]
        fn_name: str = call.function.name
        try:
            fn_args: dict[str, Any] = json.loads(call.function.arguments)
        except json.JSONDecodeError as exc:
            raise AppError(
                "LLM_PROVIDER_ERROR",
                "The model returned invalid tool arguments.",
                502,
            ) from exc

        return {"tool_name": fn_name, "arguments": fn_args}

    async def _call_chat_completion(self, use_case: str, **kwargs: Any) -> Any:
        client = self._get_client()
        attempts = self.settings.llm_max_retries
        last_error: Exception | None = None

        kwargs.setdefault("model", self.settings.openai_model)
        kwargs.setdefault("timeout", self.settings.llm_timeout_seconds)

        for attempt in range(1, attempts + 1):
            started = time.perf_counter()
            try:
                response = await client.chat.completions.create(**kwargs)
                latency_ms = int((time.perf_counter() - started) * 1000)
                logger.info(
                    "llm_call_finished",
                    extra={
                        "use_case": use_case,
                        "model": self.settings.openai_model,
                        "latency_ms": latency_ms,
                        "attempt": attempt,
                        "success": True,
                    },
                )
                return response
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "llm_call_failed",
                    extra={
                        "use_case": use_case,
                        "model": self.settings.openai_model,
                        "attempt": attempt,
                        "success": False,
                        "error_type": exc.__class__.__name__,
                    },
                )
                if attempt >= attempts:
                    break
                await asyncio.sleep(min(0.5 * (2 ** (attempt - 1)), 4))

        if last_error and "timeout" in last_error.__class__.__name__.lower():
            raise AppError("LLM_TIMEOUT", "LLM request timed out.", 504)
        raise AppError("LLM_PROVIDER_ERROR", "LLM provider request failed.", 502)

    async def _complete_text(
        self,
        use_case: str,
        messages: list[dict[str, str]],
        response_format: dict[str, str] | None = None,
    ) -> str:
        extra: dict[str, Any] = {}
        if response_format:
            extra["response_format"] = response_format
        response = await self._call_chat_completion(use_case, messages=messages, **extra)
        return response.choices[0].message.content or ""
