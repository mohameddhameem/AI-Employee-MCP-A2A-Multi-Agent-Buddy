#!/usr/bin/env python3
"""
SDK integration tests for MainAgent using the official A2A SDK endpoints.
Skips gracefully if SDK modules are not importable.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import pytest
from fastapi.testclient import TestClient

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from agents.main_agent_a2a import MainAgentA2A


@pytest.fixture(autouse=True)
def isolate_a2a_sdk_imports(monkeypatch):
    import sys as _sys

    removed_entries = []
    project_pkg_path = str(project_root)
    for entry in (project_pkg_path, ""):
        if entry in _sys.path:
            _sys.path.remove(entry)
            removed_entries.append(entry)

    evicted = {}
    for name in list(_sys.modules.keys()):
        if name == "a2a" or name.startswith("a2a."):
            evicted[name] = _sys.modules[name]
            del _sys.modules[name]

    monkeypatch.setenv("USE_A2A_SDK", "true")

    try:
        yield
    finally:
        for entry in reversed(removed_entries):
            if entry not in _sys.path:
                _sys.path.insert(0 if entry == "" else len(_sys.path), entry)
        for name, mod in evicted.items():
            _sys.modules.setdefault(name, mod)


def _sdk_available() -> bool:
    removed_entries = []
    project_pkg_path = str(project_root)
    for entry in (project_pkg_path, ""):
        if entry in sys.path:
            sys.path.remove(entry)
            removed_entries.append(entry)
    try:
        import importlib

        last_error = None
        for ns in ("a2a", "a2a_sdk"):
            try:
                importlib.import_module(f"{ns}.server.apps.jsonrpc.fastapi_app")
                importlib.import_module(f"{ns}.server.request_handlers.default_request_handler")
                importlib.import_module(f"{ns}.server.tasks.inmemory_task_store")
                importlib.import_module(f"{ns}.server.agent_execution.agent_executor")
                importlib.import_module(f"{ns}.server.agent_execution.context")
                importlib.import_module(f"{ns}.types")
                importlib.import_module(f"{ns}.utils.message")
                return True
            except Exception as e:
                last_error = e
                continue
        if last_error:
            pytest.skip(f"SDK modules not importable: {last_error}")
        return False
    finally:
        for entry in reversed(removed_entries):
            if entry not in sys.path:
                sys.path.insert(0 if entry == "" else len(sys.path), entry)


def _build_sdk_app(host: str = "localhost", port: int = 28001):
    if not _sdk_available():
        pytest.skip("a2a-sdk not installed; skipping SDK integration tests")
    os.environ["USE_A2A_SDK"] = "true"
    agent = MainAgentA2A()
    try:
        app = agent.build_app(host, port)
    except ModuleNotFoundError:
        pytest.skip("a2a-sdk modules not found at runtime; skipping")
    return agent, app


def _extract_task_id(result: Dict[str, Any]) -> Optional[str]:
    if not isinstance(result, dict):
        return None
    if isinstance(result.get("id"), str):
        return result["id"]
    task = result.get("task")
    if isinstance(task, dict) and isinstance(task.get("id"), str):
        return task.get("id")
    if isinstance(result.get("taskId"), str):
        return result.get("taskId")
    return None


def test_sdk_agent_card_shape_main():
    agent, app = _build_sdk_app()
    client = TestClient(app)

    resp = client.get("/.well-known/agent-card.json")
    assert resp.status_code == 200
    data = resp.json()

    assert data.get("name") == agent.name
    assert data.get("url") and data["url"].startswith("http://")
    pt = data.get("preferred_transport") or data.get("preferredTransport")
    assert pt == "jsonrpc"


def test_sdk_message_send_blocking_main():
    _, app = _build_sdk_app()
    client = TestClient(app)

    req = {
        "jsonrpc": "2.0",
        "id": "mb1",
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "messageId": "m-mb1",
                "parts": [{"kind": "text", "text": "hello"}],
            },
            "configuration": {"blocking": True},
        },
    }
    resp = client.post("/a2a", json=req)
    assert resp.status_code == 200
    payload = resp.json()
    assert payload.get("jsonrpc") == "2.0"
    assert payload.get("id") == "mb1"
    assert "result" in payload


def test_sdk_message_send_nonblocking_and_tasks_get_main():
    _, app = _build_sdk_app()
    client = TestClient(app)

    send_req = {
        "jsonrpc": "2.0",
        "id": "mnb1",
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "messageId": "m-mnb1",
                "parts": [{"kind": "text", "text": "department summary"}],
            },
            "configuration": {"blocking": False},
        },
    }
    send_resp = client.post("/a2a", json=send_req)
    assert send_resp.status_code == 200
    send_payload = send_resp.json()
    result = send_payload.get("result")
    assert result is not None
    task_id = _extract_task_id(result)
    if not task_id:
        pytest.skip("SDK response shape did not expose a task id; skipping follow-up calls")

    get_req = {
        "jsonrpc": "2.0",
        "id": "mg1",
        "method": "tasks/get",
        "params": {"id": task_id, "historyLength": 1},
    }
    get_resp = client.post("/a2a", json=get_req)
    assert get_resp.status_code in (200, 404)
    get_payload = get_resp.json()
    assert get_payload.get("jsonrpc") == "2.0"
    assert get_payload.get("id") == "mg1"
    if get_resp.status_code == 200 and "error" in get_payload:
        assert get_payload["error"].get("code") == -32001
    else:
        assert get_payload.get("result") is not None


def test_sdk_tasks_cancel_flow_main():
    _, app = _build_sdk_app()
    client = TestClient(app)

    send_req = {
        "jsonrpc": "2.0",
        "id": "mc1",
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "messageId": "m-mc1",
                "parts": [{"kind": "text", "text": "tell me something"}],
            },
            "configuration": {"blocking": False},
        },
    }
    send_resp = client.post("/a2a", json=send_req)
    assert send_resp.status_code == 200
    task_id = _extract_task_id(send_resp.json().get("result", {}))
    if not task_id:
        pytest.skip("SDK response shape did not expose a task id; skipping cancel flow")

    cancel_req = {
        "jsonrpc": "2.0",
        "id": "mc2",
        "method": "tasks/cancel",
        "params": {"id": task_id},
    }
    cancel_resp = client.post("/a2a", json=cancel_req)
    assert cancel_resp.status_code in (200, 400, 404)
    payload = cancel_resp.json()
    assert payload.get("jsonrpc") == "2.0"
    assert payload.get("id") == "mc2"
    if cancel_resp.status_code == 200:
        if "error" in payload:
            assert payload["error"].get("code") == -32001
        else:
            assert "result" in payload
    else:
        assert "error" in payload
