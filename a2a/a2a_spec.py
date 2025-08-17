#!/usr/bin/env python3
"""
DEPRECATED: Minimal A2A spec-compliant primitives for JSON-RPC transport.
Implements:
- JSON-RPC 2.0 request/response helpers
- Core data types: Task, TaskStatus/TaskState, Message, TextPart
- In-memory TaskStore (submit/get/cancel)

Historically used to expose a legacy /a2a/v1 endpoint with methods:
- message/send
- tasks/get
- tasks/cancel

The official A2A SDK now serves JSON-RPC at /a2a by default. This module is kept for
reference and potential offline testing, but is no longer wired into the running agents
unless explicitly used in legacy mode.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

# ------------------------- JSON-RPC helpers -------------------------

JSONRPC_VERSION = "2.0"


def jsonrpc_success(id_: Union[str, int], result: Any) -> Dict[str, Any]:
    return {"jsonrpc": JSONRPC_VERSION, "id": id_, "result": result}


def jsonrpc_error(
    id_: Optional[Union[str, int]], code: int, message: str, data: Any | None = None
) -> Dict[str, Any]:
    err: Dict[str, Any] = {
        "jsonrpc": JSONRPC_VERSION,
        "id": id_,
        "error": {"code": code, "message": message},
    }
    if data is not None:
        err["error"]["data"] = data
    return err


# JSON-RPC error codes
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603

# A2A-specific error codes (-32000 to -32099)
TASK_NOT_FOUND = -32001
TASK_NOT_CANCELABLE = -32002
UNSUPPORTED_OPERATION = -32004


# ------------------------- A2A Data Types -------------------------


class TaskState(str, Enum):
    Submitted = "submitted"
    Working = "working"
    InputRequired = "input-required"
    Completed = "completed"
    Canceled = "canceled"
    Failed = "failed"
    Rejected = "rejected"
    AuthRequired = "auth-required"
    Unknown = "unknown"


@dataclass
class TextPart:
    kind: str
    text: str

    @staticmethod
    def make(text: str) -> "TextPart":
        return TextPart(kind="text", text=text)


Part = TextPart  # minimal for phase 1


@dataclass
class Message:
    role: str  # "user" | "agent"
    parts: List[Part]
    messageId: str
    taskId: Optional[str] = None
    contextId: Optional[str] = None
    kind: str = field(default="message", init=False)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TaskStatus:
    state: TaskState
    message: Optional[Message] = None
    timestamp: Optional[str] = None


@dataclass
class Task:
    id: str
    contextId: str
    status: TaskStatus
    history: List[Message] = field(default_factory=list)
    artifacts: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    kind: str = field(default="task", init=False)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # Convert enums to values
        d["status"]["state"] = (
            self.status.state.value
            if isinstance(self.status.state, TaskState)
            else self.status.state
        )
        return d


# ------------------------- In-memory Task Store -------------------------


class TaskStore:
    def __init__(self) -> None:
        self._tasks: Dict[str, Task] = {}

    def create_from_message(
        self, message: Message, blocking: bool = False, handler=None
    ) -> Union[Message, Task]:
        """Create a task for the message or return a direct Message result if blocking and fast.
        The handler is a callable(message) -> str (text response) for quick ops.
        """
        # Quick path: if blocking and a handler is provided, return a direct agent Message
        if blocking and handler is not None:
            response_text = handler(message)
            reply = Message(
                role="agent", parts=[TextPart.make(response_text)], messageId=str(uuid.uuid4())
            )
            return reply

        # Create task
        task_id = str(uuid.uuid4())
        ctx_id = message.contextId or str(uuid.uuid4())
        message.taskId = task_id
        message.contextId = ctx_id

        status = TaskStatus(
            state=TaskState.Submitted, timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )
        task = Task(id=task_id, contextId=ctx_id, status=status, history=[message])
        self._tasks[task_id] = task
        return task

    def get(self, task_id: str, history_length: Optional[int] = None) -> Task:
        if task_id not in self._tasks:
            raise KeyError("Task not found")
        task = self._tasks[task_id]
        if history_length is not None and history_length >= 0:
            trimmed = list(task.history)[-history_length:]
            task_copy = Task(
                id=task.id,
                contextId=task.contextId,
                status=task.status,
                history=trimmed,
                artifacts=task.artifacts,
                metadata=task.metadata,
            )
            return task_copy
        return task

    def cancel(self, task_id: str) -> Task:
        if task_id not in self._tasks:
            raise KeyError("Task not found")
        task = self._tasks[task_id]
        if task.status.state in (
            TaskState.Completed,
            TaskState.Canceled,
            TaskState.Failed,
            TaskState.Rejected,
        ):
            # not cancelable
            raise ValueError("Task cannot be canceled")
        task.status.state = TaskState.Canceled
        task.status.timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        return task


# ------------------------- Parameter validation -------------------------


def parse_message_send_params(params: Dict[str, Any]) -> Tuple[Message, Dict[str, Any]]:
    if not isinstance(params, dict) or "message" not in params:
        raise ValueError("Invalid params: missing 'message'")
    m = params["message"]
    if not isinstance(m, dict):
        raise ValueError("Invalid params: 'message' must be object")
    role = m.get("role")
    parts = m.get("parts")
    msg_id = m.get("messageId") or str(uuid.uuid4())
    if role not in ("user", "agent"):
        raise ValueError("Invalid message.role")
    if not isinstance(parts, list) or not parts:
        raise ValueError("Invalid message.parts")
    # Only TextPart for phase 1
    norm_parts: List[TextPart] = []
    for p in parts:
        if not isinstance(p, dict) or p.get("kind") != "text" or "text" not in p:
            raise ValueError("Only TextPart is supported in phase 1")
        norm_parts.append(TextPart.make(str(p["text"])))
    message = Message(
        role=role,
        parts=norm_parts,
        messageId=msg_id,
        taskId=m.get("taskId"),
        contextId=m.get("contextId"),
    )
    configuration = (
        params.get("configuration", {}) if isinstance(params.get("configuration", {}), dict) else {}
    )
    return message, configuration


def parse_tasks_get_params(params: Dict[str, Any]) -> Tuple[str, Optional[int]]:
    if not isinstance(params, dict) or "id" not in params:
        raise ValueError("Invalid params: missing 'id'")
    task_id = str(params["id"])
    history_length = params.get("historyLength")
    if history_length is not None:
        try:
            history_length = int(history_length)
        except Exception:
            raise ValueError("Invalid historyLength")
    return task_id, history_length


def parse_tasks_cancel_params(params: Dict[str, Any]) -> str:
    if not isinstance(params, dict) or "id" not in params:
        raise ValueError("Invalid params: missing 'id'")
    return str(params["id"])
