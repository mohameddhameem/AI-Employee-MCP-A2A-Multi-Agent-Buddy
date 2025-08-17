#!/usr/bin/env python3
"""
SDK integration tests for HRAgent using the official A2A SDK endpoints.
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

from agents.hr_agent_a2a import HRAgentA2A


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


def _build_sdk_app(host: str = "localhost", port: int = 28002):
    if not _sdk_available():
        pytest.skip("a2a-sdk not installed; skipping SDK integration tests")
    os.environ["USE_A2A_SDK"] = "true"
    agent = HRAgentA2A()
    try:
        app = agent.build_app(host, port)
    except ModuleNotFoundError:
        pytest.skip("a2a-sdk modules not found at runtime; skipping")
    return agent, app


def test_sdk_agent_card_shape_hr():
    agent, app = _build_sdk_app()
    client = TestClient(app)

    resp = client.get("/.well-known/agent-card.json")
    assert resp.status_code == 200
    data = resp.json()

    assert data.get("name") == agent.name
    assert data.get("url") and data["url"].startswith("http://")
    # Support both snake_case and camelCase serialization
    preferred_transport = data.get("preferred_transport") or data.get("preferredTransport")
    assert preferred_transport == "jsonrpc"


def test_sdk_message_send_blocking_hr():
    _, app = _build_sdk_app()
    client = TestClient(app)

    req = {
        "jsonrpc": "2.0",
        "id": "hb1",
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "messageId": "m-hb1",
                "parts": [{"kind": "text", "text": "department summary"}],
            },
            "configuration": {"blocking": True},
        },
    }
    resp = client.post("/a2a", json=req)
    assert resp.status_code == 200
    payload = resp.json()
    assert payload.get("jsonrpc") == "2.0"
    assert payload.get("id") == "hb1"
    assert "result" in payload
