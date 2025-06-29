"""
Phase 3: MCP Server Implementation
FastMCP server that exposes employee database via Model Context Protocol
"""

from fastmcp import FastMCP
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from data.database_utils import EmployeeDB

# Initialize FastMCP server
mcp = FastMCP("Employee Database Server")

# Initialize database connection
try:
    db_path = project_root / "data" / "employees.db"
    db = EmployeeDB(str(db_path))
    print(f"✅ Connected to employee database at {db_path}")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    sys.exit(1)

# Pydantic models for structured responses
class Employee(BaseModel):
    id: int
    name: str
    department: str
    salary: int
    email: str
    hire_date: str
    manager_id: Optional[int]
    location: str

class Department(BaseModel):
    department: str
    employee_count: int
    avg_salary: float
    min_salary: int
    max_salary: int

class Project(BaseModel):
    id: int
    name: str
    description: str
    status: str
    budget: int
    start_date: str
    end_date: Optional[str]
    department_name: str

# MCP Resources - Static data the agent can read
@mcp.resource("employees://all")
def get_all_employees_resource() -> str:
    """Resource containing all employee data"""
    employees = db.get_all_employees()
    return f"""# All Employees Database

This resource contains information about all {len(employees)} employees in the company.

## Departments:
- Engineering: 5 employees
- Data Science: 4 employees  
- Sales: 4 employees
- Marketing: 3 employees
- HR: 2 employees
- Finance: 2 employees

## Employee List:
{chr(10).join([f"- {emp['name']} ({emp['department']}) - ${emp['salary']:,}" for emp in employees])}

## Usage:
Use the employee query tools to get detailed information about specific employees or departments.
"""

@mcp.resource("employees://departments")
def get_departments_resource() -> str:
    """Resource containing department summary"""
    summary = db.get_department_summary()
    
    content = "# Department Summary\n\n"
    for dept in summary:
        content += f"## {dept['department']}\n"
        content += f"- Employees: {dept['employee_count']}\n"
        content += f"- Average Salary: ${dept['avg_salary']:,.0f}\n"
        content += f"- Salary Range: ${dept['min_salary']:,} - ${dept['max_salary']:,}\n\n"
    
    return content

@mcp.resource("employees://projects")
def get_projects_resource() -> str:
    """Resource containing active projects"""
    projects = db.get_active_projects()
    
    content = "# Active Projects\n\n"
    for proj in projects:
        content += f"## {proj['name']}\n"
        content += f"- Department: {proj['department_name']}\n"
        content += f"- Budget: ${proj['budget']:,}\n"
        content += f"- Status: {proj['status']}\n"
        content += f"- Description: {proj['description']}\n\n"
    
    return content

# MCP Tools - Functions the agent can call
@mcp.tool()
def get_all_employees() -> List[Dict[str, Any]]:
    """Get all employees in the company"""
    return db.get_all_employees()

@mcp.tool()  
def get_employees_by_department(department: str) -> List[Dict[str, Any]]:
    """
    Get all employees in a specific department
    
    Args:
        department: Department name (Engineering, Marketing, Sales, HR, Finance, Data Science)
    """
    return db.get_employees_by_department(department)

@mcp.tool()
def get_employee_by_id(employee_id: int) -> Optional[Dict[str, Any]]:
    """
    Get employee details by ID
    
    Args:
        employee_id: Unique employee identifier
    """
    return db.get_employee_by_id(employee_id)

@mcp.tool()
def get_department_summary() -> List[Dict[str, Any]]:
    """Get summary statistics for all departments"""
    return db.get_department_summary()

@mcp.tool()
def get_employees_by_salary_range(min_salary: int, max_salary: int) -> List[Dict[str, Any]]:
    """
    Get employees within a salary range
    
    Args:
        min_salary: Minimum salary (inclusive)
        max_salary: Maximum salary (inclusive)
    """
    return db.get_employees_by_salary_range(min_salary, max_salary)

@mcp.tool()
def search_employees(search_term: str) -> List[Dict[str, Any]]:
    """
    Search employees by name or email
    
    Args:
        search_term: Search string to match against name or email
    """
    return db.search_employees(search_term)

@mcp.tool()
def get_managers_and_reports() -> List[Dict[str, Any]]:
    """Get all managers with their direct reports"""
    return db.get_managers_and_reports()

@mcp.tool()
def get_employee_summary() -> Dict[str, Any]:
    """Get overall employee statistics and summary"""
    return db.get_employee_summary()

@mcp.tool()
def get_active_projects() -> List[Dict[str, Any]]:
    """Get all active projects with department information"""
    return db.get_active_projects()

@mcp.tool()
def get_high_earners(threshold: int = 100000) -> List[Dict[str, Any]]:
    """
    Get employees earning above a certain threshold
    
    Args:
        threshold: Salary threshold (default: $100,000)
    """
    return db.get_employees_by_salary_range(threshold, 999999)

# Health check tool
@mcp.tool()
def health_check() -> Dict[str, str]:
    """Check if the MCP server and database are working"""
    try:
        count = len(db.get_all_employees())
        return {
            "status": "healthy",
            "database": "connected", 
            "employee_count": str(count),
            "message": "MCP server is running correctly"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "error",
            "error": str(e),
            "message": "MCP server has issues"
        }

if __name__ == "__main__":
    import asyncio
    
    print("🚀 Starting MCP Server...")
    print("=" * 40)
    print("📋 Available Resources:")
    print("  - employees://all")
    print("  - employees://departments") 
    print("  - employees://projects")
    print()
    print("🔧 Available Tools:")
    print("  - get_all_employees()")
    print("  - get_employees_by_department(department)")
    print("  - get_employee_by_id(id)")
    print("  - get_department_summary()")
    print("  - search_employees(search_term)")
    print("  - get_managers_and_reports()")
    print("  - get_employee_summary()")
    print("  - get_active_projects()")
    print("  - health_check()")
    print()
    print("🌐 Server will start on http://localhost:8000")
    print("📡 MCP endpoint: http://localhost:8000/mcp")
    
    # Run the server with HTTP transport
    try:
        asyncio.run(mcp.run_http_async(
            transport="http",
            host="localhost", 
            port=8000,
            path="/mcp"
        ))
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
