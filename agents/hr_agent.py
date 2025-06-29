#!/usr/bin/env python3
"""
Phase 5: HRAgent - Specialized Human Resources Agent
Handles all employee-related queries and HR operations
"""

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

# HR-specific tool functions
def get_all_employees() -> str:
    """Get all employees from the database"""
    result = mcp_wrapper.call_tool("get_all_employees")
    if isinstance(result, list):
        return f"📋 Employee Directory ({len(result)} total employees):\n" + "\n".join([
            f"👤 {emp.get('name', 'Unknown')} - {emp.get('department', 'Unknown')} Dept. - ${emp.get('salary', 0):,}/year"
            for emp in result
        ])
    return str(result)

def get_employees_by_department(department: str) -> str:
    """Get employees by department with HR formatting"""
    result = mcp_wrapper.call_tool("get_employees_by_department", {"department": department})
    if isinstance(result, list):
        total_salary = sum(emp.get('salary', 0) for emp in result)
        avg_salary = total_salary / len(result) if result else 0
        
        response = f"🏢 {department} Department Overview:\n"
        response += f"👥 Team Size: {len(result)} employees\n"
        response += f"💰 Average Salary: ${avg_salary:,.0f}\n"
        response += f"💼 Total Department Payroll: ${total_salary:,}\n\n"
        response += "👤 Team Members:\n"
        
        for emp in result:
            response += f"  • {emp.get('name', 'Unknown')} - ${emp.get('salary', 0):,} - {emp.get('email', 'No email')}\n"
        
        return response
    return str(result)

def get_department_summary() -> str:
    """Get HR-focused department summary"""
    result = mcp_wrapper.call_tool("get_department_summary")
    if isinstance(result, list):
        summary = "🏢 HR Department Analytics:\n"
        summary += "=" * 40 + "\n"
        
        total_employees = sum(dept.get('employee_count', 0) for dept in result)
        total_payroll = sum(dept.get('avg_salary', 0) * dept.get('employee_count', 0) for dept in result)
        
        summary += f"👥 Total Workforce: {total_employees} employees\n"
        summary += f"💰 Total Company Payroll: ${total_payroll:,.0f}/year\n"
        summary += f"📊 Average Company Salary: ${total_payroll/total_employees:,.0f}/year\n\n"
        
        summary += "📋 Department Breakdown:\n"
        for dept in sorted(result, key=lambda x: x.get('employee_count', 0), reverse=True):
            summary += f"  🏢 {dept.get('department', 'Unknown')}: "
            summary += f"{dept.get('employee_count', 0)} employees @ ${dept.get('avg_salary', 0):,.0f} avg\n"
        
        return summary
    return str(result)

def search_employees(search_term: str) -> str:
    """Search for employees with HR context"""
    result = mcp_wrapper.call_tool("search_employees", {"search_term": search_term})
    if isinstance(result, list):
        if not result:
            return f"🔍 No employees found matching '{search_term}'"
        
        response = f"🔍 Search Results for '{search_term}' ({len(result)} found):\n"
        for emp in result:
            response += f"👤 {emp.get('name', 'Unknown')} - {emp.get('department', 'Unknown')} - "
            response += f"${emp.get('salary', 0):,} - Hired: {emp.get('hire_date', 'Unknown')}\n"
        return response
    return str(result)

def get_managers_and_reports() -> str:
    """Get organizational hierarchy"""
    result = mcp_wrapper.call_tool("get_managers_and_reports")
    if isinstance(result, list):
        response = "👑 Organizational Hierarchy:\n"
        response += "=" * 30 + "\n"
        
        # Group by manager
        managers = {}
        for emp in result:
            manager_id = emp.get('manager_id')
            if manager_id not in managers:
                managers[manager_id] = []
            managers[manager_id].append(emp)
        
        for manager_id, employees in managers.items():
            if manager_id is None:
                response += "🏢 Executive Level:\n"
            else:
                response += f"👤 Manager ID {manager_id}:\n"
            
            for emp in employees:
                response += f"  • {emp.get('name', 'Unknown')} - {emp.get('department', 'Unknown')}\n"
            response += "\n"
        
        return response
    return str(result)

# HR Agent class
class HRAgent:
    """Specialized Human Resources Agent"""
    
    def __init__(self, name: str = "HRAgent"):
        self.name = name
        self.tools = {
            "get_all_employees": get_all_employees,
            "get_employees_by_department": get_employees_by_department,
            "get_department_summary": get_department_summary,
            "search_employees": search_employees,
            "get_managers_and_reports": get_managers_and_reports
        }
    
    def process_query(self, query: str) -> str:
        """Process HR-specific queries"""
        query_lower = query.lower()
        
        # HR-specific routing logic
        if any(word in query_lower for word in ["hierarchy", "manager", "reports", "org chart", "organizational"]):
            return self.tools["get_managers_and_reports"]()
            
        elif any(word in query_lower for word in ["payroll", "salary", "budget", "analytics", "summary"]):
            return self.tools["get_department_summary"]()
            
        elif any(dept in query_lower for dept in ["engineering", "marketing", "sales", "hr", "finance", "data science"]):
            # Extract department name
            for dept in ["Engineering", "Marketing", "Sales", "HR", "Finance", "Data Science"]:
                if dept.lower() in query_lower:
                    return self.tools["get_employees_by_department"](dept)
                    
        elif any(word in query_lower for word in ["search", "find", "lookup"]):
            # Extract search term
            words = query.split()
            if len(words) > 1:
                search_term = words[-1]
                return self.tools["search_employees"](search_term)
                
        elif any(word in query_lower for word in ["all", "everyone", "directory", "list"]):
            return self.tools["get_all_employees"]()
            
        else:
            # Default HR response
            return """🏢 HR Assistant at your service! I can help with:
            
👤 Employee Information:
  • "List all employees" - Complete employee directory
  • "Show Engineering team" - Department-specific listings
  • "Search for Smith" - Find specific employees
  
📊 HR Analytics:
  • "Department summary" - Payroll and headcount analytics
  • "Organizational hierarchy" - Management structure
  • "Salary analysis" - Compensation insights
  
💼 How can I assist you with HR matters today?"""
    
    def serve(self, host: str = "localhost", port: int = 8002):
        """Start HTTP server for the HR agent"""
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        from pydantic import BaseModel
        import uvicorn
        
        app = FastAPI(title=f"{self.name} API", description="Specialized Human Resources Agent")
        
        class TaskRequest(BaseModel):
            input: str
        
        @app.post("/task")
        async def handle_task(request: TaskRequest):
            try:
                result = self.process_query(request.input)
                return JSONResponse({
                    "status": "success",
                    "result": result,
                    "agent": self.name,
                    "specialization": "Human Resources"
                })
            except Exception as e:
                return JSONResponse({
                    "status": "error",
                    "error": str(e),
                    "agent": self.name
                }, status_code=500)
        
        @app.get("/health")
        async def health_check():
            return {
                "status": "healthy", 
                "agent": self.name,
                "specialization": "Human Resources",
                "capabilities": list(self.tools.keys())
            }
        
        @app.get("/")
        async def root():
            return {
                "agent": self.name,
                "specialization": "Human Resources",
                "description": "Specialized agent for employee data, organizational structure, and HR analytics",
                "endpoints": {
                    "POST /task": "Process HR queries",
                    "GET /health": "Health check",
                    "GET /": "Agent information"
                },
                "sample_queries": [
                    "List all employees",
                    "Show Engineering team",
                    "Department summary",
                    "Organizational hierarchy",
                    "Search for employee name"
                ]
            }
        
        print(f"🏢 Starting {self.name} on http://{host}:{port}")
        print("📋 HR Specializations:")
        print("  👤 Employee directory and search")
        print("  🏢 Department analytics and payroll")
        print("  👑 Organizational hierarchy")
        print("  📊 HR metrics and summaries")
        
        uvicorn.run(app, host=host, port=port)

# Create the HR agent
hr_agent = HRAgent()

if __name__ == "__main__":
    print("🏢 HRAgent - Human Resources Specialist")
    print("=" * 40)
    print("🔧 Specialized HR Tools:")
    print("  - Employee directory management")
    print("  - Department analytics")
    print("  - Organizational hierarchy")
    print("  - Payroll analysis")
    print("  - Employee search and lookup")
    print()
    print(f"🌐 Connecting to MCP Server: {MCP_BASE_URL}")
    
    # Test MCP connection
    try:
        test_result = mcp_wrapper.call_tool("health_check")
        print(f"✅ MCP Server Status: Connected")
    except Exception as e:
        print(f"⚠️  MCP Server connection issue: {e}")
    
    print()
    
    # Start the HR agent server
    host = os.getenv("HR_AGENT_HOST", "localhost")
    port = int(os.getenv("HR_AGENT_PORT", "8002"))
    
    hr_agent.serve(host=host, port=port)
