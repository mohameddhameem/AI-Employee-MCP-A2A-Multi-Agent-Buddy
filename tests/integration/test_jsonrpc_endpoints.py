#!/usr/bin/env python3
"""
DEPRECATED: Legacy JSON-RPC integration tests for /a2a/v1 methods.
This file is retained for historical reference but is skipped by default
since the project now uses the official A2A SDK at /a2a.
"""

import pytest

pytestmark = pytest.mark.skip(reason="Legacy /a2a/v1 tests removed; SDK /a2a is default")

import sys
from pathlib import Path
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from agents.greeting_agent_a2a import GreetingAgentA2A  # noqa: F401
from agents.hr_agent_a2a import HRAgentA2A  # noqa: F401
from agents.main_agent_a2a import MainAgentA2A  # noqa: F401


# Ensure baseline tests run against legacy/spec-aligned JSON-RPC implementation, not SDK
@pytest.fixture(autouse=True)
def disable_a2a_sdk(monkeypatch):
    monkeypatch.setenv("USE_A2A_SDK", "false")


@pytest.mark.parametrize(
    "agent_cls, host, port",
    [
        (HRAgentA2A, "localhost", 18002),
        (GreetingAgentA2A, "localhost", 18003),
        (MainAgentA2A, "localhost", 18001),
    ],
)
def test_message_send_blocking(agent_cls, host, port):
    agent = agent_cls()
    app = agent.build_app(host, port)
    client = TestClient(app)

    # Blocking = true should return a Message from agent
    req = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": "hello"}],
                "messageId": "m1",
            },
            "configuration": {"blocking": True},
        },
    }
    resp = client.post("/a2a/v1", json=req)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("result"), data
    result = data["result"]
    # For blocking path, we expect a message shape (role/parts/messageId)
    assert result.get("role") == "agent"
    assert isinstance(result.get("parts"), list) and result["parts"], result


@pytest.mark.parametrize(
    "agent_cls, host, port",
    [
        (HRAgentA2A, "localhost", 18002),
        (GreetingAgentA2A, "localhost", 18003),
        (MainAgentA2A, "localhost", 18001),
    ],
)
def test_message_send_nonblocking_and_tasks_get(agent_cls, host, port):
    agent = agent_cls()
    app = agent.build_app(host, port)
    client = TestClient(app)

    # Non-blocking should create a Task
    req = {
        "jsonrpc": "2.0",
        "id": "2",
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": "department summary"}],
                # Let server assign messageId
            },
            "configuration": {"blocking": False},
        },
    }
    resp = client.post("/a2a/v1", json=req)
    assert resp.status_code == 200
    result = resp.json()["result"]
    assert result.get("kind") == "task", result
    task_id = result["id"]

    # tasks/get with historyLength
    get_req = {
        "jsonrpc": "2.0",
        "id": "3",
        "method": "tasks/get",
        "params": {"id": task_id, "historyLength": 1},
    }
    get_resp = client.post("/a2a/v1", json=get_req)
    assert get_resp.status_code == 200
    task = get_resp.json()["result"]
    assert task["id"] == task_id
    assert isinstance(task.get("history"), list)
    assert len(task["history"]) <= 1


@pytest.mark.parametrize(
    "agent_cls, host, port",
    [
        (HRAgentA2A, "localhost", 18002),
        (GreetingAgentA2A, "localhost", 18003),
        (MainAgentA2A, "localhost", 18001),
    ],
)
def test_tasks_cancel_noncancelable(agent_cls, host, port):
    agent = agent_cls()
    app = agent.build_app(host, port)
    client = TestClient(app)

    # Create non-blocking task
    send_req = {
        "jsonrpc": "2.0",
        "id": "4",
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": "list all employees"}],
            },
            "configuration": {"blocking": False},
        },
    }
    send_resp = client.post("/a2a/v1", json=send_req)
    assert send_resp.status_code == 200
    task_id = send_resp.json()["result"]["id"]

    # Cancel task (first cancel should succeed)
    cancel_req = {"jsonrpc": "2.0", "id": "5", "method": "tasks/cancel", "params": {"id": task_id}}
    cancel_resp = client.post("/a2a/v1", json=cancel_req)
    assert cancel_resp.status_code == 200
    canceled = cancel_resp.json()["result"]
    assert canceled["status"]["state"] == "canceled"

    # Cancel again should be non-cancelable
    cancel_again = client.post("/a2a/v1", json=cancel_req)
    assert cancel_again.status_code == 400
    err = cancel_again.json().get("error", {})
    assert err.get("code") == -32002  # TASK_NOT_CANCELABLE


def test_agent_card_shapes():
    # Only test HR agent for shape; others share same schema shape
    agent = HRAgentA2A()
    app = agent.build_app("localhost", 18002)
    client = TestClient(app)

    resp = client.get("/.well-known/agent-card.json")
    assert resp.status_code == 200
    data = resp.json()

    # Basic shape checks aligned with tightened schema
    assert data.get("agentId") == agent.agent_id
    assert data.get("agentName") == agent.name
    assert data.get("agentType") == agent.agent_type
    assert data.get("a2a", {}).get("version") == "1.0"
    assert data.get("a2a", {}).get("transport") == "jsonrpc-2.0"
    assert "/a2a/v1" in data.get("a2a", {}).get("rpcUrl", "")
    assert "health" in data.get("endpoints", {})
