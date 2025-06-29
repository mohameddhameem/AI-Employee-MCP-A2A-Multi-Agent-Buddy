"""
Phase 4: Single RAG Agent with ADK + MCP Integration
Defines a MainAgent that calls MCP server tools
"""
import os
from dotenv import load_dotenv
import requests
from google_adk import LlmAgent, tool

# Load environment variables
load_dotenv()

# Configure MCP endpoint
MCP_HOST = os.getenv("MCP_SERVER_HOST", "localhost")
MCP_PORT = os.getenv("MCP_SERVER_PORT", "8000")
MCP_URL = f"http://{MCP_HOST}:{MCP_PORT}/mcp"

@tool(name="get_all_employees", description="Retrieve all employees from the database")
def get_all_employees() -> list:
    payload = {"method": "tools/call", "params": {"name": "get_all_employees", "arguments": {}}}
    resp = requests.post(MCP_URL, json=payload).json()
    return resp.get("result") or resp

@tool(name="get_employees_by_department", description="Get employees by department")
def get_employees_by_department(department: str) -> list:
    payload = {"method": "tools/call", "params": {"name": "get_employees_by_department", "arguments": {"department": department}}}
    resp = requests.post(MCP_URL, json=payload).json()
    return resp.get("result") or resp

if __name__ == "__main__":
    # Create and start the ADK agent
    agent = LlmAgent(
        name="MainAgent",
        llm=os.getenv("OPENAI_API_KEY"),  # Provide API key or provider config
        tools=[get_all_employees, get_employees_by_department],
        description="You are a company assistant. Use tools to answer HR queries."
    )
    # Run HTTP API server for agent
    host = os.getenv("ADK_AGENT_HOST", "localhost")
    port = int(os.getenv("ADK_AGENT_PORT", "8001"))
    print(f"🚀 Starting MainAgent on http://{host}:{port}")
    agent.run(host=host, port=port)
