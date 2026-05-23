from fastapi.testclient import TestClient

from app.main import app
from app.services.llm_service import _string_list
from app.schemas import FormAssistantResponse, Meta


client = TestClient(app)


class FakeLLMService:
    def __init__(self):
        self.form_calls = []

    async def suggest_form_values(self, context: str) -> FormAssistantResponse:
        self.form_calls.append(context)
        return FormAssistantResponse(
            project_name="AI Primitives",
            target_user="Product builders",
            problem="AI logic lives in frontend routes",
            proposed_solution="Move structured AI flows into FastAPI endpoints",
            main_risks=["Contracts can drift"],
            success_metric="Frontend calls backend endpoints only",
            meta=Meta(model="test-model", latency_ms=1),
        )


def teardown_function():
    if hasattr(app.state, "llm_service"):
        del app.state.llm_service


def test_empty_context_returns_unified_validation_error():
    response = client.post("/form-assistant", json={"context": ""})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_short_context_returns_unified_validation_error():
    response = client.post("/form-assistant", json={"context": "short"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_valid_request_calls_service_layer_and_returns_structured_response():
    service = FakeLLMService()
    app.state.llm_service = service

    response = client.post(
        "/form-assistant",
        json={"context": "Move another structured AI flow into the backend."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["project_name"] == "AI Primitives"
    assert body["target_user"] == "Product builders"
    assert body["problem"] == "AI logic lives in frontend routes"
    assert body["proposed_solution"] == "Move structured AI flows into FastAPI endpoints"
    assert body["main_risks"] == ["Contracts can drift"]
    assert body["success_metric"] == "Frontend calls backend endpoints only"
    assert service.form_calls == [
        "Move another structured AI flow into the backend."
    ]


def test_string_risk_is_not_split_into_characters():
    assert _string_list("Technology risk") == ["Technology risk"]
