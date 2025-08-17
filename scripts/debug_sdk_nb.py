import os
import sys

from fastapi.testclient import TestClient

# Ensure project root import
sys.path.append(".")
from agents.greeting_agent_a2a import GreetingAgentA2A

os.environ["USE_A2A_SDK"] = "true"

a = GreetingAgentA2A()
app = a.build_app("localhost", 28003)
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

r = client.post("/a2a", json=send_req)
print("send status", r.status_code)
print("send json", r.json())

result = r.json().get("result", {})
# try to find task id in several shapes

task_id = None
if isinstance(result, dict):
    for k in ("id", "taskId"):
        if isinstance(result.get(k), str):
            task_id = result.get(k)
            break
    if not task_id and isinstance(result.get("task"), dict):
        task_id = result["task"].get("id")
print("task_id", task_id)

if task_id:
    get_req = {
        "jsonrpc": "2.0",
        "id": "g1",
        "method": "tasks/get",
        "params": {"id": task_id, "historyLength": 1},
    }
    gr = client.post("/a2a", json=get_req)
    print("get status", gr.status_code)
    print("get json", gr.json())
else:
    print("no task id in result")
