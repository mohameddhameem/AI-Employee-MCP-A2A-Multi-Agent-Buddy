import inspect
import os
import sys

# remove project root from sys.path to avoid local 'a2a' shadowing
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
try:
    sys.path.remove(project_root)
except ValueError:
    pass

import importlib

print("Inspecting A2A SDK symbols...")
mods = {
    "types": "a2a.types",
    "fastapi_app": "a2a.server.apps.jsonrpc.fastapi_app",
    "default_handler": "a2a.server.request_handlers.default_request_handler",
    "inmemory_task_store": "a2a.server.tasks.inmemory_task_store",
    "agent_executor": "a2a.server.agent_execution.agent_executor",
    "context": "a2a.server.agent_execution.context",
    "events_queue": "a2a.server.events.event_queue",
    "events_consumer": "a2a.server.events.event_consumer",
    "request_handler": "a2a.server.request_handlers.request_handler",
    "response_helpers": "a2a.server.request_handlers.response_helpers",
}
loaded = {}
for k, v in mods.items():
    try:
        loaded[k] = importlib.import_module(v)
        print("OK", k, "->", v)
    except Exception as e:
        print("FAIL", k, v, e)

# Print helpful classes and functions
T = loaded.get("types")
if T:
    print("\nTypes:", [n for n in dir(T) if n[0].isupper()][:50])
    for attr in ["AgentCard", "AgentCapabilities", "AgentSkill", "Message"]:
        obj = getattr(T, attr, None)
        if obj:
            print(attr, "->", obj)
    # Show model fields for key types (pydantic v2):
    for attr in ["Message", "DataPart", "Task", "TaskStatusUpdateEvent"]:
        obj = getattr(T, attr, None)
        if obj is not None:
            fields = getattr(obj, "model_fields", None)
            if fields:
                print(f"{attr}.model_fields:", list(fields.keys()))

ctx = loaded.get("context")
if ctx:
    for attr in dir(ctx):
        if "message" in attr.lower() or "context" in attr.lower():
            print("context attr:", attr)

ae = loaded.get("agent_executor")
if ae:
    print("\nAgentExecutor bases:", [n for n in dir(ae) if "Executor" in n])

rh = loaded.get("response_helpers")
if rh:
    print("\nResponse helpers:", [n for n in dir(rh) if not n.startswith("_")])

q = loaded.get("events_queue")
if q:
    print("\nEventQueue attrs:", [n for n in dir(q) if not n.startswith("_")])
    EQ = getattr(q, "EventQueue", None)
    if EQ:
        print("EventQueue.enqueue_event signature:", inspect.signature(EQ.enqueue_event))

cons = loaded.get("events_consumer")
if cons:
    print("\nEvent consumer attrs:", [n for n in dir(cons) if not n.startswith("_")])
