#!/usr/bin/env python3
"""
Phase 6: A2A-Enhanced HRAgent
HR Agent with Agent-to-Agent protocol support for standardized communication
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict

import requests
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging
from common.logging_config import configure_logging

# Initialize logging
configure_logging()
logger = logging.getLogger(__name__)

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from a2a.protocol import A2AMessage, A2AProtocol, AgentCapability, MessageType

# Legacy JSON-RPC helpers removed; SDK handles JSON-RPC at /a2a


# NOTE: The official A2A SDK package is named 'a2a' (distribution: a2a-sdk),
# which collides with this repo's local 'a2a' package. Provide a dynamic import
# helper to temporarily remove the project root from sys.path so site-packages
# resolves, and support both 'a2a' and 'a2a_sdk' namespaces.
def _load_a2a_sdk_modules():
    import importlib

    def _try_namespace(ns: str):
        candidates = [
            (
                f"{ns}.server.apps.jsonrpc.fastapi_app",
                f"{ns}.server.request_handlers.default_request_handler",
                f"{ns}.server.tasks.inmemory_task_store",
                f"{ns}.server.agent_execution.agent_executor",
                f"{ns}.server.agent_execution.context",
                f"{ns}.types",
                f"{ns}.utils.message",
            ),
        ]
        for (
            fastapi_app_path,
            default_handler_path,
            inmemory_store_path,
            agent_exec_path,
            ctx_path,
            types_path,
            msg_utils_path,
        ) in candidates:
            try:
                types_mod = importlib.import_module(types_path)
                fastapi_app_mod = importlib.import_module(fastapi_app_path)
                default_handler_mod = importlib.import_module(default_handler_path)
                inmemory_store_mod = importlib.import_module(inmemory_store_path)
                agent_exec_mod = importlib.import_module(agent_exec_path)
                ctx_mod = importlib.import_module(ctx_path)
                msg_utils = importlib.import_module(msg_utils_path)
                return {
                    "types": types_mod,
                    "fastapi_app": fastapi_app_mod,
                    "default_handler": default_handler_mod,
                    "inmemory_store": inmemory_store_mod,
                    "agent_executor": agent_exec_mod,
                    "ctx": ctx_mod,
                    "msg_utils": msg_utils,
                }
            except Exception:
                continue
        return None

    project_pkg_path = str(project_root)
    removed_entries = []
    for entry in (project_pkg_path, ""):
        if entry in sys.path:
            try:
                sys.path.remove(entry)
                removed_entries.append(entry)
            except ValueError:
                pass
    try:
        # Evict local 'a2a' modules from sys.modules if they originate from the project path
        to_delete = []
        proj_str = str(project_root)
        for name, mod in list(sys.modules.items()):
            if not name.startswith("a2a"):
                continue
            try:
                mod_path = getattr(mod, "__file__", None) or (getattr(mod, "__path__", [None])[0])
            except Exception:
                mod_path = None
            if isinstance(mod_path, str) and proj_str in mod_path:
                to_delete.append(name)
        for name in to_delete:
            sys.modules.pop(name, None)
        for ns in ("a2a", "a2a_sdk"):
            sdk = _try_namespace(ns)
            if sdk:
                return sdk
    finally:
        for entry in reversed(removed_entries):
            if entry not in sys.path:
                sys.path.insert(0 if entry == "" else len(sys.path), entry)

    for ns in ("a2a_sdk",):
        sdk = _try_namespace(ns)
        if sdk:
            return sdk

    raise ModuleNotFoundError("Could not locate A2A SDK modules under 'a2a' or 'a2a_sdk'")


# Load environment variables
load_dotenv()


class MCPToolWrapper:
    """Wrapper for MCP server tools with HTTP communication"""

    def __init__(self, mcp_url: str):
        self.mcp_url = mcp_url

    def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call an MCP tool via HTTP"""
        try:
            payload = {
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": arguments or {}},
            }

            response = requests.post(
                self.mcp_url, json=payload, headers={"Content-Type": "application/json"}, timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if "result" in data:
                    return data["result"]
                else:
                    return {"error": "No result in MCP response", "response": data}
            else:
                return {"error": f"MCP server returned {response.status_code}"}

        except Exception as e:
            return {"error": f"MCP call failed: {str(e)}"}


class HRAgentA2A:
    """A2A-Enhanced HR Agent specialized for employee data and analytics"""

    def __init__(self, name: str = "HRAgent"):
        self.name = name
        self.agent_id = "hr_agent_specialist"
        self.agent_type = "domain_specialist"
        self.specialization = "Human Resources"
        self.port = int(os.getenv("HR_AGENT_PORT", "8002"))
        self.endpoint = f"http://localhost:{self.port}"

        # Initialize A2A protocol
        self.a2a = A2AProtocol(
            agent_id=self.agent_id,
            agent_name=self.name,
            endpoint=self.endpoint,
            secret_key=os.getenv("A2A_SECRET_KEY", "rag_a2a_mcp_secret"),
        )

        # MCP connection
        mcp_url = f"http://localhost:{os.getenv('MCP_SERVER_PORT', '8000')}/mcp"
        self.mcp = MCPToolWrapper(mcp_url)

        # Define HR capabilities for A2A protocol
        self.capabilities = [
            AgentCapability(
                name="employee_directory",
                description="Access and search employee directory information",
                input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
                output_schema={"type": "object", "properties": {"employees": {"type": "array"}}},
                keywords=["employee", "staff", "directory", "search", "find"],
                confidence_level=0.95,
            ),
            AgentCapability(
                name="department_analytics",
                description="Analyze department data, payroll, and organizational metrics",
                input_schema={"type": "object", "properties": {"department": {"type": "string"}}},
                output_schema={"type": "object", "properties": {"analytics": {"type": "object"}}},
                keywords=["department", "analytics", "payroll", "salary", "metrics"],
                confidence_level=0.9,
            ),
            AgentCapability(
                name="organizational_hierarchy",
                description="Display organizational structure and reporting relationships",
                input_schema={"type": "object"},
                output_schema={"type": "object", "properties": {"hierarchy": {"type": "object"}}},
                keywords=["hierarchy", "organization", "manager", "reports", "structure"],
                confidence_level=0.85,
            ),
        ]

        # Override A2A protocol handlers
        self.a2a._handle_capability_query = self._handle_capability_query_override
        self.a2a._handle_delegation_request = self._handle_delegation_request_override

    def _handle_capability_query_override(self, message) -> Dict[str, Any]:
        """Override capability query to return HR-specific capabilities"""

        capabilities_data = [
            {
                "name": cap.name,
                "description": cap.description,
                "input_schema": cap.input_schema,
                "output_schema": cap.output_schema,
                "keywords": cap.keywords,
                "confidence_level": cap.confidence_level,
            }
            for cap in self.capabilities
        ]

        response = self.a2a.create_message(
            MessageType.CAPABILITY_RESPONSE,
            message.sender_id,
            {
                "agent_type": self.agent_type,
                "specialization": self.specialization,
                "capabilities": capabilities_data,
            },
            correlation_id=message.correlation_id,
        )

        return response.to_dict()

    def _handle_delegation_request_override(self, message: A2AMessage) -> Dict[str, Any]:
        """Handle HR task delegation with specialized processing"""

        payload = message.payload
        task = payload.get("task", "")
        context = payload.get("context", {})

        # Process the HR task
        result = self.process_hr_query(task)

        response = self.a2a.create_message(
            MessageType.DELEGATION_RESPONSE,
            message.sender_id,
            {
                "status": "success",
                "result": result,
                "agent": self.agent_id,
                "specialization": self.specialization,
                "processed_via": "a2a_delegation",
            },
            correlation_id=message.correlation_id,
        )

        return response.to_dict()

    def _extract_data_from_mcp_result(self, result: Any, expected_type: str = "list") -> Any:
        """
        Helper method to extract data from MCP server response
        Handles both direct responses and wrapped responses
        """
        # Handle error cases
        if isinstance(result, dict) and "error" in result:
            return None

        # If result is already the expected type, return it
        if expected_type == "list" and isinstance(result, list):
            return result
        elif expected_type == "dict" and isinstance(result, dict) and "content" not in result:
            return result
        if isinstance(result, dict):
            return result.get("content", [] if expected_type == "list" else {})
        return [] if expected_type == "list" else {}

    def process_hr_query(self, query: str) -> str:
        """Process HR queries with enhanced formatting"""
        # Normalize query for routing logic
        query_lower = query.lower()

    # Enhanced query routing with A2A context
        if any(word in query_lower for word in ["list", "all employees", "everyone", "directory"]):
            return self._get_formatted_employee_list()

        elif any(word in query_lower for word in ["engineering", "department", "team"]):
            dept_match = None
            for dept in ["engineering", "data science", "marketing", "sales"]:
                if dept in query_lower:
                    dept_match = dept
                    break

            if dept_match:
                return self._get_department_overview(dept_match.title())
            else:
                return self._get_all_departments_summary()

        elif any(word in query_lower for word in ["summary", "analytics", "overview"]):
            return self._get_hr_analytics_summary()

        elif any(
            word in query_lower for word in ["hierarchy", "organization", "manager", "reports"]
        ):
            return self._get_organizational_hierarchy()

        elif any(word in query_lower for word in ["search", "find"]):
            # Extract search term
            search_terms = ["search for", "find", "search", "look for"]
            search_term = query_lower
            for term in search_terms:
                if term in query_lower:
                    search_term = query_lower.split(term)[-1].strip()
                    break

            return self._search_employees(search_term)

        else:
            # Default: try to find any employee name or department mentioned
            return self._smart_search(query)

    def _get_formatted_employee_list(self) -> str:
        """Get formatted list of all employees"""
        result = self.mcp.call_tool("get_all_employees")

        # Use helper to extract data
        employees = self._extract_data_from_mcp_result(result, "list")

        if employees is None:
            return f"Error accessing employee data: {result.get('error', 'Unknown error')}"

        if not employees:
            return "No employees found in the database."

        response = f"Employee Directory ({len(employees)} total employees):\n"

        for emp in employees:
            name = emp.get("name", "Unknown")
            dept = emp.get("department", "Unknown")
            salary = emp.get("salary", 0)

            response += f"{name} - {dept} Dept. - ${salary:,}/year\n"

        return response

    def _get_department_overview(self, department: str) -> str:
        """Get detailed department overview"""
        result = self.mcp.call_tool("get_employees_by_department", {"department": department})

        employees = self._extract_data_from_mcp_result(result, "list")

        if employees is None:
            return f"Error accessing {department} data: {result.get('error', 'Unknown error')}"

        if not employees:
            return f"No employees found in {department} department."

        # Calculate analytics
        total_employees = len(employees)
        total_salary = sum(emp.get("salary", 0) for emp in employees)
        avg_salary = total_salary // total_employees if total_employees > 0 else 0

        response = f"{department} Department Overview:\n"
        response += f"Team Size: {total_employees} employees\n"
        response += f"Average Salary: ${avg_salary:,}\n"
        response += f"Total Department Payroll: ${total_salary:,}\n\n"
        response += f"Team Members:\n"

        for emp in employees:
            name = emp.get("name", "Unknown")
            salary = emp.get("salary", 0)
            hire_date = emp.get("hire_date", "Unknown")

            response += f"  - {name} - ${salary:,}/year - Hired: {hire_date}\n"

        return response

    def _get_all_departments_summary(self) -> str:
        """Get summary of all departments"""
        result = self.mcp.call_tool("get_department_summary")

        dept_data = self._extract_data_from_mcp_result(result, "dict")

        if dept_data is None:
            return f"Error accessing department data: {result.get('error', 'Unknown error')}"

        if not dept_data:
            return "No department data available."

        # Get total employee count
        all_employees_result = self.mcp.call_tool("get_all_employees")
        all_employees = self._extract_data_from_mcp_result(all_employees_result, "list")
        total_employees = len(all_employees) if all_employees else 0

        response = "HR Department Analytics:\n"
        response += "=" * 40 + "\n"
        response += f"Total Workforce: {total_employees} employees\n\n"

        for dept, info in dept_data.items():
            count = info.get("count", 0)
            avg_salary = info.get("avg_salary", 0)
            total_salary = info.get("total_salary", 0)

            response += f"**{dept}**\n"
            response += f"  Employees: {count}\n"
            response += f"  Average Salary: ${avg_salary:,}\n"
            response += f"  Department Payroll: ${total_salary:,}\n\n"

        return response

    def _get_hr_analytics_summary(self) -> str:
        """Get comprehensive HR analytics"""
        # Get all employees for overall stats
        all_result = self.mcp.call_tool("get_all_employees")
        dept_result = self.mcp.call_tool("get_department_summary")

        employees = self._extract_data_from_mcp_result(all_result, "list")
        dept_data = self._extract_data_from_mcp_result(dept_result, "dict")

        if employees is None or dept_data is None:
            return "Error accessing HR analytics data"

        total_employees = len(employees)
        total_payroll = sum(emp.get("salary", 0) for emp in employees)
        avg_company_salary = total_payroll // total_employees if total_employees > 0 else 0

        response = "HR Department Analytics:\n"
        response += "=" * 40 + "\n"
        response += f"Total Workforce: {total_employees} employees\n"
        response += f"Total Company Payroll: ${total_payroll:,}/year\n"
        response += f"Average Company Salary: ${avg_company_salary:,}/year\n"
        response += f"Active Departments: {len(dept_data)}\n\n"

        response += "Department Breakdown:\n"
        for dept, info in dept_data.items():
            count = info.get("count", 0)
            percentage = (count / total_employees * 100) if total_employees > 0 else 0
            response += f"  - {dept}: {count} employees ({percentage:.1f}%)\n"

        return response

    def _get_organizational_hierarchy(self) -> str:
        """Get organizational hierarchy"""
        result = self.mcp.call_tool("get_managers_and_reports")

        hierarchy = self._extract_data_from_mcp_result(result, "dict")

        if hierarchy is None:
            return f"Error accessing hierarchy data: {result.get('error', 'Unknown error')}"

        if not hierarchy:
            return "No organizational hierarchy data available."

        response = "Organizational Hierarchy:\n"
        response += "=" * 30 + "\n"

        for manager_id, reports in hierarchy.items():
            if reports:  # Only show managers with reports
                response += f"Manager ID {manager_id}:\n"
                for report in reports:
                    name = report.get("name", "Unknown")
                    dept = report.get("department", "Unknown")
                    response += f"- {name} - {dept}\n"
                response += "\n"

        return response

    def _search_employees(self, search_term: str) -> str:
        """Search for employees"""
        result = self.mcp.call_tool("search_employees", {"search_term": search_term})

        employees = self._extract_data_from_mcp_result(result, "list")

        if employees is None:
            return f"Search failed: {result.get('error', 'Unknown error')}"

        if not employees:
            return f"No employees found matching '{search_term}'"

        response = f"Search Results for '{search_term}' ({len(employees)} found):\n"

        for emp in employees:
            name = emp.get("name", "Unknown")
            dept = emp.get("department", "Unknown")
            salary = emp.get("salary", 0)
            hire_date = emp.get("hire_date", "Unknown")

            response += f"{name} - {dept} - ${salary:,} - Hired: {hire_date}\n"

        return response

    def _smart_search(self, query: str) -> str:
        """Intelligent search based on query content"""
        # Try searching for any potential names or keywords in the query
        words = query.split()

        for word in words:
            if len(word) > 2:  # Only search meaningful words
                result = self.mcp.call_tool("search_employees", {"search_term": word})

                employees = self._extract_data_from_mcp_result(result, "list")

                if employees:
                    return self._format_search_results(word, employees)

        # Fallback to general HR help
                return """I can help you with HR queries! Try asking:

**Employee Information:**
    - "List all employees"
    - "Search for Alice" 
    - "Find John"

**Department Data:**
    - "Show Engineering team"
    - "Department summary"
    - "Marketing department"

**Analytics:**
    - "HR analytics"
    - "Organizational hierarchy"
    - "Payroll summary"

**Tip:** Be specific about what employee or department information you need!"""

    def _format_search_results(self, term: str, employees: list) -> str:
        """Format search results"""
        response = f"Found {len(employees)} result(s) for '{term}':\n"

        for emp in employees:
            name = emp.get("name", "Unknown")
            dept = emp.get("department", "Unknown")
            salary = emp.get("salary", 0)

            response += f"{name} - {dept} - ${salary:,}/year\n"

        return response

    def build_app(self, host: str, port: int) -> FastAPI:
        """Build and return the FastAPI app with all routes (for serving and tests)."""
        app = FastAPI(title=f"{self.name} A2A API", description="A2A-Enhanced HR Specialist Agent")
        base_url = f"http://{host}:{port}"

        # Migration feature flag: if enabled, mount SDK /a2a and agent-card
        USE_A2A_SDK = os.getenv("USE_A2A_SDK", "false").lower() in {"1", "true", "yes"}

        if USE_A2A_SDK:
            sdk = _load_a2a_sdk_modules()

            AgentCard = sdk["types"].AgentCard
            AgentCapabilities = getattr(sdk["types"], "AgentCapabilities")
            AgentSkill = getattr(sdk["types"], "AgentSkill")

            # Map HR capabilities to SDK AgentSkill entries
            skills = []
            for cap in self.capabilities:
                skills.append(
                    AgentSkill(
                        id=cap.name,
                        name=cap.name,
                        description=cap.description,
                        tags=cap.keywords or [],
                        input_modes=["text"],
                        output_modes=["text"],
                    )
                )

            card = AgentCard(
                name=self.name,
                description="HR specialist for employee data and analytics",
                url=base_url,
                version="1.0.0",
                protocol_version="1.0",
                preferred_transport="jsonrpc",
                default_input_modes=["text"],
                default_output_modes=["text"],
                capabilities=AgentCapabilities(
                    streaming=False,
                    state_transition_history=False,
                    push_notifications=False,
                ),
                skills=skills,
                supports_authenticated_extended_card=False,
            )

            AgentExecutorBase = sdk["agent_executor"].AgentExecutor
            get_message_text = sdk["ctx"].get_message_text
            new_agent_text_message = sdk["msg_utils"].new_agent_text_message

            class HRAgentExecutor(AgentExecutorBase):
                def __init__(self, outer: "HRAgentA2A"):
                    self.outer = outer

                async def execute(self, context, event_queue) -> None:
                    text = get_message_text(context.message) if context.message else ""
                    reply = self.outer.process_hr_query(text or "")
                    msg = new_agent_text_message(
                        text=reply,
                        context_id=context.context_id,
                        task_id=context.task_id,
                    )
                    await event_queue.enqueue_event(msg)

                async def cancel(self, context, event_queue) -> None:
                    msg = new_agent_text_message(
                        text="Cancellation acknowledged. No ongoing task to cancel.",
                        context_id=context.context_id,
                        task_id=context.task_id,
                    )
                    await event_queue.enqueue_event(msg)

            DefaultRequestHandler = sdk["default_handler"].DefaultRequestHandler
            InMemoryTaskStore = sdk["inmemory_store"].InMemoryTaskStore
            A2AFastAPIApplication = sdk["fastapi_app"].A2AFastAPIApplication

            handler = DefaultRequestHandler(
                agent_executor=HRAgentExecutor(self),
                task_store=InMemoryTaskStore(),
            )
            sdk_app = A2AFastAPIApplication(agent_card=card, http_handler=handler)
            sdk_app.add_routes_to_app(
                app,
                agent_card_url="/.well-known/agent-card.json",
                rpc_url="/a2a",
            )

        class TaskRequest(BaseModel):
            input: str

        @app.post("/task")
        async def handle_task(request: TaskRequest):
            try:
                result = self.process_hr_query(request.input)
                return JSONResponse(
                    {
                        "status": "success",
                        "result": result,
                        "agent": self.name,
                        "specialization": self.specialization,
                        "protocol": "http",
                    }
                )
            except Exception as e:
                return JSONResponse(
                    {"status": "error", "error": str(e), "agent": self.name}, status_code=500
                )

        if not USE_A2A_SDK:

            @app.post("/a2a")
            async def handle_a2a_message(request: Request):
                """Handle incoming A2A protocol messages"""
                try:
                    message_data = await request.json()
                    response = self.a2a.handle_incoming_message(message_data)
                    return JSONResponse(response)
                except Exception as e:
                    return JSONResponse(
                        {"error": "message_processing_failed", "details": str(e)}, status_code=500
                    )

        @app.get("/health")
        async def health_check():
            # Test MCP connection
            mcp_status = "connected"
            try:
                test_result = self.mcp.call_tool("health_check")
                if "error" in test_result:
                    mcp_status = "error"
            except:
                mcp_status = "disconnected"

            return {
                "status": "healthy",
                "agent": self.name,
                "specialization": self.specialization,
                "mcp_status": mcp_status,
                "a2a_protocol": "enabled",
                "capabilities": len(self.capabilities),
            }

        @app.get("/capabilities")
        async def get_capabilities():
            """Get HR agent capabilities"""
            return {
                "agent_id": self.agent_id,
                "agent_name": self.name,
                "specialization": self.specialization,
                "capabilities": [
                    {
                        "name": cap.name,
                        "description": cap.description,
                        "keywords": cap.keywords,
                        "confidence_level": cap.confidence_level,
                    }
                    for cap in self.capabilities
                ],
            }

        @app.get("/")
        async def root():
            return {
                "agent": self.name,
                "specialization": self.specialization,
                "description": "A2A-enhanced HR specialist for employee data and analytics",
                "capabilities": [cap.name for cap in self.capabilities],
                "a2a_protocol": "enabled",
                "endpoints": {
                    "POST /task": "Process HR queries",
                    "POST /a2a": "A2A protocol message handling",
                    # JSON-RPC served by SDK at POST /a2a when enabled
                    "GET /.well-known/agent-card.json": "Agent Card (A2A discovery)",
                    "GET /health": "Health check with MCP status",
                    "GET /capabilities": "HR capabilities information",
                    "GET /": "Agent information",
                },
            }

        return app

    def serve(self, host: str = "localhost", port: int = None):
        """Start A2A-enhanced HR Agent server"""
        if port is None:
            port = self.port

        app = self.build_app(host, port)

        logger.info(f"Starting {self.name} (A2A-Enhanced) on http://{host}:{port}")
        logger.info("A2A-Enhanced HR Capabilities:")
        for cap in self.capabilities:
            logger.debug(f"  {cap.name}: {cap.description}")
        logger.debug("Connecting to MCP Server: http://localhost:8000")

        # Test MCP connection
        test_result = self.mcp.call_tool("health_check")
        if "error" not in test_result:
            logger.info("MCP Server Status: Connected")
        else:
            logger.warning(f"MCP Server Status: {test_result.get('error')}")

        logger.info("A2A Protocol: Enabled")
        logger.info(f"Message Authentication: {'Enabled' if self.a2a.secret_key else 'Disabled'}")

        uvicorn.run(app, host=host, port=port)


# Instantiate and serve in __main__
if __name__ == "__main__":
    logger.info("A2A-Enhanced HRAgent - Human Resources Specialist")
    logger.info("%s", '=' * 55)
    logger.info("Phase 6 A2A Enhancements:")
    logger.info("  A2A protocol communication support")
    logger.info("  Secure message authentication")
    logger.info("  Detailed capability advertisement")
    logger.info("  Enhanced health monitoring")
    logger.info("  Delegation request handling")

    hr_agent_a2a = HRAgentA2A()
    host = os.getenv("HR_AGENT_HOST", "localhost")
    port = int(os.getenv("HR_AGENT_PORT", "8002"))
    hr_agent_a2a.serve(host, port)
