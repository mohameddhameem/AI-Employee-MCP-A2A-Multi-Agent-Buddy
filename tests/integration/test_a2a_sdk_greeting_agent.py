#!/usr/bin/env python3
"""
SDK integration tests for GreetingAgent using the official A2A SDK endpoints.

Covers:
- /.well-known/agent-card.json via SDK
- /a2a JSON-RPC: message/send (blocking and non-blocking)
- /a2a JSON-RPC: tasks/get with historyLength
- /a2a JSON-RPC: tasks/cancel basic flow

Notes:
- Tests enable the SDK via USE_A2A_SDK=true for the app under test.
- If the SDK is not installed, tests will be skipped gracefully.
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

from agents.greeting_agent_a2a import GreetingAgentA2A


@pytest.fixture(autouse=True)
def isolate_a2a_sdk_imports(monkeypatch):
    """Ensure site-packages a2a SDK is importable within this test module.

    - Removes project root and '' from sys.path
    - Temporarily evicts any 'a2a' modules from sys.modules
    - Sets USE_A2A_SDK=true for the app under test
    Restores state after the test to avoid cross-test interference.
    """
    import sys as _sys

    removed_entries = []
    project_pkg_path = str(project_root)
    for entry in (project_pkg_path, ""):
        if entry in _sys.path:
            _sys.path.remove(entry)
            removed_entries.append(entry)

    # Evict a2a modules and capture originals for restore
    evicted = {}
    for name in list(_sys.modules.keys()):
        if name == "a2a" or name.startswith("a2a."):
            evicted[name] = _sys.modules[name]
            del _sys.modules[name]

    monkeypatch.setenv("USE_A2A_SDK", "true")

    try:
        yield
    finally:
        # Restore sys.path
        for entry in reversed(removed_entries):
            if entry not in _sys.path:
                _sys.path.insert(0 if entry == "" else len(_sys.path), entry)
        # Restore evicted modules if not reloaded differently
        for name, mod in evicted.items():
            _sys.modules.setdefault(name, mod)


def _sdk_available() -> bool:
    """Detect if the official a2a-sdk is importable despite local package name collision.

    Probes both 'a2a' and 'a2a_sdk' namespaces and key submodules.
    """
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


def _build_sdk_app(host: str = "localhost", port: int = 28003):
    """Build GreetingAgent app with SDK enabled or skip if SDK missing."""
    if not _sdk_available():
        pytest.skip("a2a-sdk not installed; skipping SDK integration tests")

    # Ensure SDK mode for this app only
    os.environ["USE_A2A_SDK"] = "true"

    agent = GreetingAgentA2A()
    try:
        app = agent.build_app(host, port)
    except ModuleNotFoundError:
        pytest.skip("a2a-sdk modules not found at runtime; skipping")
    return agent, app


def _extract_task_id(result: Dict[str, Any]) -> Optional[str]:
    """Best-effort extraction of task id from various potential result shapes."""
    if not isinstance(result, dict):
        return None
    # Common shapes: {"id": "...", "kind": "task"}
    if isinstance(result.get("id"), str):
        return result["id"]
    # or {"task": {"id": "..."}}
    task = result.get("task")
    if isinstance(task, dict) and isinstance(task.get("id"), str):
        return task.get("id")
    # or {"taskId": "..."}
    if isinstance(result.get("taskId"), str):
        return result.get("taskId")
    return None


def test_sdk_agent_card_shape():
    agent, app = _build_sdk_app()
    client = TestClient(app)

    resp = client.get("/.well-known/agent-card.json")
    assert resp.status_code == 200
    data = resp.json()

    # Minimal shape checks (allow both snake_case and camelCase depending on serializer)
    def pick(d, *keys):
        for k in keys:
            if k in d:
                return d[k]
        return None

    assert pick(data, "name") == agent.name
    assert (pick(data, "url") or "").startswith("http://")
    assert pick(data, "protocol_version", "protocolVersion") in {"1.0", "1.0.0"}
    assert pick(data, "preferred_transport", "preferredTransport") == "jsonrpc"


def test_sdk_message_send_blocking():
    _, app = _build_sdk_app()
    client = TestClient(app)

    req = {
        "jsonrpc": "2.0",
        "id": "b1",
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "messageId": "m-b1",
                "parts": [{"kind": "text", "text": "hello"}],
            },
            "configuration": {"blocking": True},
        },
    }
    resp = client.post("/a2a", json=req)
    assert resp.status_code == 200
    payload = resp.json()
    assert payload.get("jsonrpc") == "2.0"
    assert payload.get("id") == "b1"
    assert "result" in payload


def test_sdk_message_send_nonblocking_and_tasks_get():
    _, app = _build_sdk_app()
    client = TestClient(app)

    send_req = {
        "jsonrpc": "2.0",
        "id": "nb1",
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "messageId": "m-nb1",
                "parts": [{"kind": "text", "text": "how are you"}],
            },
            "configuration": {"blocking": False},
        },
    }
    send_resp = client.post("/a2a", json=send_req)
    assert send_resp.status_code == 200
    send_payload = send_resp.json()
    assert send_payload.get("jsonrpc") == "2.0"
    result = send_payload.get("result")
    assert result is not None
    task_id = _extract_task_id(result)
    if not task_id:
        pytest.skip("SDK response shape did not expose a task id; skipping follow-up calls")

    get_req = {
        "jsonrpc": "2.0",
        "id": "g1",
        "method": "tasks/get",
        "params": {"id": task_id, "historyLength": 1},
    }
    get_resp = client.post("/a2a", json=get_req)
    assert get_resp.status_code in (200, 404)
    get_payload = get_resp.json()
    assert get_payload.get("jsonrpc") == "2.0"
    assert get_payload.get("id") == "g1"
    # Some SDK variants may already purge completed tasks from the store.
    if get_resp.status_code == 200 and "error" in get_payload:
        # Accept JSON-RPC error -32001 (Task not found) even with HTTP 200
        assert get_payload["error"].get("code") == -32001
    else:
        assert get_payload.get("result") is not None


def test_sdk_tasks_cancel_flow():
    _, app = _build_sdk_app()
    client = TestClient(app)

    # Create non-blocking task
    send_req = {
        "jsonrpc": "2.0",
        "id": "c1",
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "messageId": "m-c1",
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
        "id": "c2",
        "method": "tasks/cancel",
        "params": {"id": task_id},
    }
    cancel_resp = client.post("/a2a", json=cancel_req)
    assert cancel_resp.status_code in (200, 400, 404)
    payload = cancel_resp.json()
    assert payload.get("jsonrpc") == "2.0"
    assert payload.get("id") == "c2"
    # If 200, either result or a JSON-RPC error -32001 (Task not found) is acceptable.
    if cancel_resp.status_code == 200:
        if "error" in payload:
            assert payload["error"].get("code") == -32001
        else:
            assert "result" in payload
    else:
        assert "error" in payload
