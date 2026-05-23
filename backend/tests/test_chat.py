from fastapi.testclient import TestClient

from app.main import app
from app.schemas import ChatMessage, ChatResponse, Meta


client = TestClient(app)


class FakeLLMService:
    def __init__(self):
        self.chat_calls = []

    async def chat(
        self,
        message: str,
        history: list[ChatMessage],
        conversation_id: str | None = None,
    ) -> ChatResponse:
        self.chat_calls.append((message, history, conversation_id))
        return ChatResponse(
            message=ChatMessage(role="assistant", content="Use a service layer."),
            conversation_id=conversation_id,
            meta=Meta(model="test-model", latency_ms=1),
        )


def teardown_function():
    if hasattr(app.state, "llm_service"):
        del app.state.llm_service


def test_empty_message_returns_unified_validation_error():
    response = client.post("/chat", json={"message": ""})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_invalid_history_role_returns_unified_validation_error():
    response = client.post(
        "/chat",
        json={
            "message": "Explain services.",
            "history": [{"role": "developer", "content": "Hidden"}],
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_valid_request_returns_assistant_message():
    service = FakeLLMService()
    app.state.llm_service = service

    response = client.post(
        "/chat",
        json={
            "message": "Explain services.",
            "conversation_id": "conv-1",
            "history": [{"role": "user", "content": "What is FastAPI?"}],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == {
        "role": "assistant",
        "content": "Use a service layer.",
    }
    assert body["conversation_id"] == "conv-1"
    assert len(service.chat_calls) == 1
    assert service.chat_calls[0][0] == "Explain services."
