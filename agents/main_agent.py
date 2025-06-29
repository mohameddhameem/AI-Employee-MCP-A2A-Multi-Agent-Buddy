import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
import requests
from typing import Dict, Any

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Load environment variables
load_dotenv()

# MCP Server Configuration
MCP_HOST = os.getenv("MCP_SERVER_HOST", "localhost")
MCP_PORT = os.getenv("MCP_SERVER_PORT", "8000")
MCP_BASE_URL = f"http://{MCP_HOST}:{MCP_PORT}"

class MCPToolWrapper:
    """Wrapper for MCP tool calls"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.mcp_url = f"{base_url}/mcp"
    
    def call_tool(self, tool_name: str, params: Dict[str, Any] = None) -> Any:
        """Call an MCP tool via HTTP"""
        payload = {
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": params or {}
            }
        }
        
        try:
            response = requests.post(
                self.mcp_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return data.get("result", data)
        except Exception as e:
            return {"error": f"MCP tool call failed: {str(e)}"}

# Initialize MCP wrapper
mcp_wrapper = MCPToolWrapper(MCP_BASE_URL)

# Tool functions
def get_all_employees() -> str:
    """Get all employees from the database"""
    result = mcp_wrapper.call_tool("get_all_employees")
    if isinstance(result, list):
        return f"Found {len(result)} employees:\n" + "\n".join([
            f"- {emp.get('name', 'Unknown')} ({emp.get('department', 'Unknown')}) - ${emp.get('salary', 0):,}"
            for emp in result[:10]  # Limit to first 10
        ])
    return str(result)

def get_employees_by_department(department: str) -> str:
    """Get employees by department"""
    result = mcp_wrapper.call_tool("get_employees_by_department", {"department": department})
    if isinstance(result, list):
        return f"Found {len(result)} employees in {department}:\n" + "\n".join([
            f"- {emp.get('name', 'Unknown')} - ${emp.get('salary', 0):,}"
            for emp in result
        ])
    return str(result)

def search_employees(search_term: str) -> str:
    """Search for employees"""
    result = mcp_wrapper.call_tool("search_employees", {"search_term": search_term})
    if isinstance(result, list):
        return f"Found {len(result)} employees matching '{search_term}':\n" + "\n".join([
            f"- {emp.get('name', 'Unknown')} ({emp.get('department', 'Unknown')})"
            for emp in result
        ])
    return str(result)

def get_department_summary() -> str:
    """Get department summary"""
    result = mcp_wrapper.call_tool("get_department_summary")
    if isinstance(result, list):
        summary = "Department Summary:\n"
        for dept in result:
            summary += f"• {dept.get('department', 'Unknown')}: {dept.get('employee_count', 0)} employees, avg ${dept.get('avg_salary', 0):,.0f}\n"
        return summary
    return str(result)

# Simple agent class
class SimpleAgent:
    """Simple agent that handles tool calls"""
    
    def __init__(self, name: str, tools: Dict[str, callable]):
        self.name = name
        self.tools = tools
    
    def process_query(self, query: str) -> str:
        """Process user query and determine which tool to use"""
        query_lower = query.lower()
        
        # Simple keyword-based routing
        if "department summary" in query_lower or "all departments" in query_lower:
            return self.tools["get_department_summary"]()
        
        elif any(dept in query_lower for dept in ["engineering", "marketing", "sales", "hr", "finance", "data science"]):
            # Extract department name
            for dept in ["Engineering", "Marketing", "Sales", "HR", "Finance", "Data Science"]:
                if dept.lower() in query_lower:
                    return self.tools["get_employees_by_department"](dept)
        
        elif "search" in query_lower or "find" in query_lower:
            # Extract search term (simple approach)
            words = query.split()
            if len(words) > 1:
                search_term = words[-1]  # Use last word as search term
                return self.tools["search_employees"](search_term)
        
        elif "all employees" in query_lower or "everyone" in query_lower:
            return self.tools["get_all_employees"]()
        
        else:
            # Default to showing all employees
            return self.tools["get_all_employees"]()
    
    def serve(self, host: str = "localhost", port: int = 8001):
        """Start HTTP server for the agent"""
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        from pydantic import BaseModel
        import uvicorn
        
        app = FastAPI(title=f"{self.name} API")
        
        class TaskRequest(BaseModel):
            input: str
        
        @app.post("/task")
        async def handle_task(request: TaskRequest):
            try:
                result = self.process_query(request.input)
                return JSONResponse({
                    "status": "success",
                    "result": result,
                    "agent": self.name
                })
            except Exception as e:
                return JSONResponse({
                    "status": "error",
                    "error": str(e),
                    "agent": self.name
                }, status_code=500)
        
        @app.get("/health")
        async def health_check():
            return {"status": "healthy", "agent": self.name}
        
        print(f"🚀 Starting {self.name} on http://{host}:{port}")
        print("📋 Available endpoints:")
        print(f"  POST http://{host}:{port}/task - Send queries")
        print(f"  GET  http://{host}:{port}/health - Health check")
        
        uvicorn.run(app, host=host, port=port)

# Create the main agent
main_agent = SimpleAgent(
    name="MainAgent",
    tools={
        "get_all_employees": get_all_employees,
        "get_employees_by_department": get_employees_by_department,
        "search_employees": search_employees,
        "get_department_summary": get_department_summary
    }
)

if __name__ == "__main__":
    print("🤖 MainAgent with MCP Integration")
    print("=" * 40)
    print("🔧 Available Tools:")
    print("  - get_all_employees()")
    print("  - get_employees_by_department(department)")
    print("  - search_employees(search_term)")
    print("  - get_department_summary()")
    print()
    print(f"🌐 Connecting to MCP Server: {MCP_BASE_URL}")
    
    # Test MCP connection
    try:
        health_result = mcp_wrapper.call_tool("health_check")
        print(f"✅ MCP Server Status: Connected")
    except Exception as e:
        print(f"⚠️  MCP Server connection issue: {e}")
    
    print()
    
    # Start the agent server
    host = os.getenv("ADK_AGENT_HOST", "localhost")
    port = int(os.getenv("ADK_AGENT_PORT", "8001"))
    
    main_agent.serve(host=host, port=port)
