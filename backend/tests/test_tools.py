from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


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
