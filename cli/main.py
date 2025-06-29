# CLI driver for MainAgent using ADK and MCP
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

# ADK agent endpoint
host = os.getenv("ADK_AGENT_HOST", "localhost")
port = os.getenv("ADK_AGENT_PORT", "8001")
agent_url = f"http://{host}:{port}"  # default ADK HTTP API root

print("🛠️  Starting CLI for MainAgent")
print(f"▶️  Sending queries to {agent_url}")
print("Type 'exit' or 'quit' to stop.")

while True:
    query = input(">>> ")
    if query.lower() in ("exit", "quit"):
        print("👋 Goodbye!")
        break

    # Send query to ADK agent
    try:
        response = requests.post(
            f"{agent_url}/task",
            json={"input": query},
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        data = response.json()
        result = data.get("result") or data.get("output") or data
        print(f"📝 Response:\n{result}\n")
    except Exception as e:
        print(f"❌ Error communicating with agent: {e}\n")
