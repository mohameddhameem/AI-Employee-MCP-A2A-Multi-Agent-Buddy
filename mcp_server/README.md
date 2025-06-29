# MCP Server

This directory contains the Model Context Protocol (MCP) server implementation that exposes the employee database.

## Files

- **`server.py`** - Main MCP server using FastMCP
- **`test_client.py`** - Test client to verify MCP functionality
- **`start_server.py`** - Simple server startup script

## MCP Resources

The server exposes these resources (static data):

- `employees://all` - All employee information
- `employees://departments` - Department summaries
- `employees://projects` - Active projects

## MCP Tools

The server provides these callable tools:

- `get_all_employees()` - Get all employees
- `get_employees_by_department(department)` - Filter by department
- `get_employee_by_id(id)` - Get specific employee
- `get_department_summary()` - Department statistics
- `search_employees(search_term)` - Search by name/email
- `get_managers_and_reports()` - Organizational hierarchy
- `get_employee_summary()` - Overall statistics
- `get_active_projects()` - Active projects
- `get_high_earners(threshold)` - High salary employees
- `health_check()` - Server health status

## Usage

### Start the Server
```bash
python mcp_server/server.py
```

### Test the Server
```bash
python mcp_server/test_client.py
```

### MCP Endpoints

- **Base URL**: http://localhost:8000
- **MCP Endpoint**: http://localhost:8000/mcp
- **Health Check**: http://localhost:8000/health

### Example MCP Request

```json
{
  "method": "tools/call",
  "params": {
    "name": "get_employees_by_department", 
    "arguments": {"department": "Engineering"}
  }
}
```

## Integration

This MCP server will be used by:
- ADK agents (Phase 4) to query employee data
- RAG systems to retrieve contextual information
- A2A protocol for agent-to-agent communication (Phase 6)
