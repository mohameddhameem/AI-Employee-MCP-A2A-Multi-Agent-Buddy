# JSON-RPC /a2a and Agent Discovery

This document describes how to use the A2A-spec JSON-RPC endpoint and discover agents via the Agent Card.

## Endpoints

- JSON-RPC (SDK): POST /a2a — JSON-RPC 2.0
- Discovery: GET /.well-known/agent-card.json

All three agents expose these endpoints: MainAgent, HRAgent, GreetingAgent.
Some agents also provide an alias at GET /.well-known/agent.json for compatibility.

## Methods

### message/send

Send a message from user or agent to the target agent. Supports blocking and non-blocking.

Request (blocking):
```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "parts": [{"kind": "text", "text": "hello"}],
      "messageId": "m1"
    },
    "configuration": {"blocking": true}
  }
}
```

Response (blocking):
```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "result": {
    "role": "agent",
    "parts": [{"kind": "text", "text": "...agent reply..."}],
    "messageId": "<uuid>"
  }
}
```

Request (non-blocking):
```json
{
  "jsonrpc": "2.0",
  "id": "2",
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "parts": [{"kind": "text", "text": "department summary"}]
    },
    "configuration": {"blocking": false}
  }
}
```

Response (non-blocking):
```json
{
  "jsonrpc": "2.0",
  "id": "2",
  "result": {
    "kind": "task",
    "id": "<task-id>",
    "contextId": "<context-id>",
    "status": {"state": "submitted", "timestamp": "..."},
    "history": [ { "role": "user", "parts": [{"kind":"text","text":"..."}], "messageId": "...", "taskId": "<task-id>" } ]
  }
}
```

### tasks/get

Get a task by id, optionally limiting history length.

```json
{
  "jsonrpc": "2.0",
  "id": "3",
  "method": "tasks/get",
  "params": {"id": "<task-id>", "historyLength": 1}
}
```

### tasks/cancel

Cancel a task. If it is already terminal (completed/canceled/failed/rejected), the server returns an error with code -32002.

```json
{
  "jsonrpc": "2.0",
  "id": "4",
  "method": "tasks/cancel",
  "params": {"id": "<task-id>"}
}
```

Error example (non-cancelable):
```json
{"jsonrpc":"2.0","id":"4","error":{"code":-32002,"message":"Task cannot be canceled"}}
```

## Agent Card

GET /.well-known/agent-card.json returns metadata for discovery.

Example:
```json
{
  "agentId": "hr_agent_specialist",
  "agentName": "HRAgent",
  "agentType": "domain_specialist",
  "specialization": "Human Resources",
  "a2a": {
    "version": "1.0",
    "transport": "jsonrpc-2.0",
  "rpcUrl": "http://localhost:8002/a2a"
  },
  "endpoints": {
    "health": "http://localhost:8002/health",
    "capabilities": "http://localhost:8002/capabilities",
    "task": "http://localhost:8002/task"
  },
  "capabilities": [
    {"name":"employee_directory","description":"...","keywords":["..."],"confidenceLevel":0.95}
  ]
}
```

Notes:
- This repo uses a minimal subset of A2A’s Agent Card fields suited to JSON-RPC usage.
- Field names align with the draft: agentId/agentName/agentType, a2a.version, a2a.transport, a2a.rpcUrl.

## Try it locally

- Start an agent (e.g., HR): it listens on HR_AGENT_PORT (default 8002)
- Discover:
  - GET http://localhost:8002/.well-known/agent-card.json
- Send JSON-RPC:
  - POST http://localhost:8002/a2a

You can also run the tests:

```pwsh
conda run --live-stream --name genai pytest -q
```
