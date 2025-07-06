#!/usr/bin/env python3
"""
HTTP-based MCP Server for Employee Database
This creates a simple HTTP API that our MainAgent can call
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from data.database_utils import EmployeeDB

# Initialize database
db_path = project_root / "data" / "employees.db"
db = EmployeeDB(str(db_path))

# FastAPI app
app = FastAPI(title="Employee Database MCP Server", version="1.0.0")

class MCPRequest(BaseModel):
    method: str
    params: Dict[str, Any]

class MCPResponse(BaseModel):
    result: Any
    error: Optional[str] = None

# Health check endpoint
@app.get("/health")
async def health_check():
    try:
        count = len(db.get_all_employees())
        return {
            "status": "healthy",
            "database": "connected",
            "employee_count": count,
            "message": "MCP server is running correctly"
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "database": "error",
            "error": str(e)
        }

# MCP endpoint
@app.post("/mcp")
async def mcp_endpoint(request: MCPRequest):
    """Handle MCP tool calls"""
    
    if request.method != "tools/call":
        raise HTTPException(status_code=400, detail="Only tools/call method supported")
    
    tool_name = request.params.get("name")
    arguments = request.params.get("arguments", {})
    
    try:
        # Route to appropriate tool function
        if tool_name == "get_all_employees":
            result = db.get_all_employees()
            
        elif tool_name == "get_employees_by_department":
            department = arguments.get("department")
            if not department:
                raise HTTPException(status_code=400, detail="department parameter required")
            result = db.get_employees_by_department(department)
            
        elif tool_name == "get_employee_by_id":
            emp_id = arguments.get("id")
            if not emp_id:
                raise HTTPException(status_code=400, detail="id parameter required")
            result = db.get_employee_by_id(emp_id)
            
        elif tool_name == "search_employees":
            search_term = arguments.get("search_term")
            if not search_term:
                raise HTTPException(status_code=400, detail="search_term parameter required")
            result = db.search_employees(search_term)
            
        elif tool_name == "get_department_summary":
            result = db.get_department_summary()
            
        elif tool_name == "get_managers_and_reports":
            result = db.get_managers_and_reports()
            
        elif tool_name == "get_employee_summary":
            result = db.get_employee_summary()
            
        elif tool_name == "get_active_projects":
            result = db.get_active_projects()
            
        elif tool_name == "health_check":
            count = len(db.get_all_employees())
            result = {
                "status": "healthy",
                "database": "connected",
                "employee_count": count,
                "message": "MCP server is running correctly"
            }
            
        else:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        
        return MCPResponse(result=result)
        
    except Exception as e:
        return MCPResponse(result=None, error=str(e))

# Root endpoint with server info
@app.get("/")
async def root():
    return {
        "name": "Employee Database MCP Server",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "mcp": "/mcp"
        },
        "tools": [
            "get_all_employees",
            "get_employees_by_department", 
            "get_employee_by_id",
            "search_employees",
            "get_department_summary",
            "get_managers_and_reports",
            "get_employee_summary",
            "get_active_projects",
            "health_check"
        ]
    }

if __name__ == "__main__":
    print("Starting HTTP-based MCP Server")
    print("=" * 40)
    print("Available Tools:")
    print("  - get_all_employees()")
    print("  - get_employees_by_department(department)")
    print("  - get_employee_by_id(id)")
    print("  - search_employees(search_term)")
    print("  - get_department_summary()")
    print("  - get_managers_and_reports()")
    print("  - get_employee_summary()")
    print("  - get_active_projects()")
    print("  - health_check()")
    print()
    print("Server starting on http://localhost:8000")
    print("MCP endpoint: http://localhost:8000/mcp")
    print("Health check: http://localhost:8000/health")
    print()
    
    # Run with uvicorn
    uvicorn.run(app, host="localhost", port=8000)
