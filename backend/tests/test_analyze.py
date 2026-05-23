from fastapi.testclient import TestClient

from app.main import app
from app.schemas import AnalyzeResponse, Meta


client = TestClient(app)


class FakeLLMService:
    def __init__(self):
        self.analyze_calls = []

    async def analyze_text(self, text: str, language: str) -> AnalyzeResponse:
        self.analyze_calls.append((text, language))
        return AnalyzeResponse(
            topics=["FastAPI", "AI backend"],
            pain_points=["AI logic lives in the frontend"],
            risks=["Routes can become too thick"],
            next_questions=["Which tools are allowed?"],
            meta=Meta(model="test-model", latency_ms=1),
        )


def teardown_function():
    if hasattr(app.state, "llm_service"):
        del app.state.llm_service


def test_empty_text_returns_unified_validation_error():
    response = client.post("/analyze", json={"text": "", "language": "ru"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_short_text_returns_unified_validation_error():
    response = client.post("/analyze", json={"text": "short", "language": "ru"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_valid_request_calls_service_layer_and_returns_structured_response():
    service = FakeLLMService()
    app.state.llm_service = service

    response = client.post(
        "/analyze",
        json={"text": "Move AI logic out of frontend components.", "language": "en"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["topics"] == ["FastAPI", "AI backend"]
    assert body["pain_points"] == ["AI logic lives in the frontend"]
    assert body["risks"] == ["Routes can become too thick"]
    assert body["next_questions"] == ["Which tools are allowed?"]
    assert service.analyze_calls == [
        ("Move AI logic out of frontend components.", "en")
    ]
