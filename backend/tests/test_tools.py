from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_plan_tool_returns_tool_plan():
    with patch(
        "app.services.llm_service.LLMService.plan_tool",
        new_callable=AsyncMock,
    ) as mock_plan:
        mock_plan.return_value = {
            "tool_name": "summarize_text",
            "arguments": {"text": "Hello world"},
        }

        response = client.post(
            "/tools/plan",
            json={"input": "Summarize this: Hello world"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["tool_name"] == "summarize_text"
        assert body["arguments"] == {"text": "Hello world"}
        assert body["requires_approval"] is False
        assert body["status"] == "planned"


def test_plan_tool_side_effect_requires_approval():
    with patch(
        "app.services.llm_service.LLMService.plan_tool",
        new_callable=AsyncMock,
    ) as mock_plan:
        mock_plan.return_value = {
            "tool_name": "save_note",
            "arguments": {"title": "Test", "content": "Content"},
        }

        response = client.post(
            "/tools/plan",
            json={"input": "Save a note titled Test"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["tool_name"] == "save_note"
        assert body["requires_approval"] is True


def test_plan_tool_unknown_tool_returns_tool_not_allowed():
    with patch(
        "app.services.llm_service.LLMService.plan_tool",
        new_callable=AsyncMock,
    ) as mock_plan:
        mock_plan.return_value = {
            "tool_name": "delete_everything",
            "arguments": {},
        }

        response = client.post(
            "/tools/plan",
            json={"input": "Delete everything"},
        )

        assert response.status_code == 403
        body = response.json()
        assert body["error"]["code"] == "TOOL_NOT_ALLOWED"
        assert body["error"]["details"] == {"tool_name": "delete_everything"}


def test_plan_tool_no_tool_selected_returns_422():
    from app.core.errors import AppError

    with patch(
        "app.services.llm_service.LLMService.plan_tool",
        new_callable=AsyncMock,
    ) as mock_plan:
        mock_plan.side_effect = AppError(
            "NO_TOOL_SELECTED",
            "The model did not select a tool.",
            422,
        )

        response = client.post(
            "/tools/plan",
            json={"input": "Hello, how are you?"},
        )

        assert response.status_code == 422
        assert response.json()["error"]["code"] == "NO_TOOL_SELECTED"


def test_plan_tool_empty_input_returns_422():
    response = client.post(
        "/tools/plan",
        json={"input": ""},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_unknown_tool_returns_tool_not_allowed():
    response = client.post(
        "/tools/execute",
        json={"tool_name": "delete_everything", "arguments": {}, "approved": True},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "TOOL_NOT_ALLOWED"


def test_side_effect_tool_without_approval_returns_approval_required():
    response = client.post(
        "/tools/execute",
        json={
            "tool_name": "save_note",
            "arguments": {"title": "AI backend", "content": "A note"},
            "approved": False,
        },
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "APPROVAL_REQUIRED"


def test_safe_tool_executes_successfully():
    response = client.post(
        "/tools/execute",
        json={
            "tool_name": "summarize_text",
            "arguments": {"text": "This is a long enough text that should be summarized."},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["tool_name"] == "summarize_text"
    assert body["status"] == "success"
    assert body["result"]["summary"]


def test_approved_side_effect_tool_executes_successfully():
    response = client.post(
        "/tools/execute",
        json={
            "tool_name": "save_note",
            "arguments": {"title": "AI backend", "content": "A note"},
            "approved": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["tool_name"] == "save_note"
    assert body["status"] == "success"
    assert body["result"]["saved"] is True
