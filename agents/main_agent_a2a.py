#!/usr/bin/env python3
"""
Phase 6: A2A-Enhanced MainAgent
MainAgent with Agent-to-Agent protocol integration for standardized communication
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
import logging
from common.logging_config import configure_logging

# Initialize logging
configure_logging()
logger = logging.getLogger(__name__)
from pydantic import BaseModel

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from a2a.protocol import A2AProtocol, AgentProfile, MessageType

# Legacy JSON-RPC helpers removed; official SDK handles JSON-RPC at /a2a


# NOTE: The official A2A SDK package is named 'a2a' (distribution: a2a-sdk),
# which collides with this repo's local 'a2a' package. Use a dynamic import helper
# to temporarily remove the project root from sys.path so site-packages resolves,
# and support both 'a2a' and 'a2a_sdk' namespaces.
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


class MainAgentA2A:
    """Enhanced MainAgent with A2A protocol support"""

    def __init__(self, name: str = "MainAgent"):
        self.name = name
        self.agent_id = "main_agent_coordinator"
        self.agent_type = "coordinator"
        self.port = int(os.getenv("MAIN_AGENT_PORT", "8001"))
        self.endpoint = f"http://localhost:{self.port}"

        # Initialize A2A protocol
        self.a2a = A2AProtocol(
            agent_id=self.agent_id,
            agent_name=self.name,
            endpoint=self.endpoint,
            secret_key=os.getenv("A2A_SECRET_KEY", "rag_a2a_mcp_secret"),
        )

        # Agent registry with A2A capabilities
        self.agent_endpoints = {
            "greeting_agent": f"http://localhost:{os.getenv('GREETING_AGENT_PORT', '8003')}",
            "hr_agent": f"http://localhost:{os.getenv('HR_AGENT_PORT', '8002')}",
        }

        # Enhanced agent specializations
        self.agent_specializations = {
            "greeting_agent": {
                "keywords": [
                    "hello",
                    "hi",
                    "hey",
                    "goodbye",
                    "bye",
                    "thank",
                    "help",
                    "who are you",
                    "how are you",
                ],
                "confidence_threshold": 0.8,
                "primary_role": "social_interaction",
            },
            "hr_agent": {
                "keywords": [
                    "employee",
                    "department",
                    "salary",
                    "payroll",
                    "hierarchy",
                    "team",
                    "staff",
                    "manager",
                    "organization",
                ],
                "confidence_threshold": 0.9,
                "primary_role": "data_specialist",
            },
        }

        # MCP server endpoint for direct fallback
        self.mcp_url = f"http://localhost:{os.getenv('MCP_SERVER_PORT', '8000')}/mcp"

    def discover_agents(self) -> Dict[str, AgentProfile]:
        """Discover agents using A2A protocol"""
        logger.info("Discovering agents using A2A protocol...")

        broadcast_endpoints = list(self.agent_endpoints.values())
        discovered_agents = self.a2a.discover_agents(broadcast_endpoints)

        logger.info("SUCCESS: Discovered %d agents via A2A protocol", len(discovered_agents))

        return {agent.agent_id: agent for agent in discovered_agents}

    def determine_best_agent_a2a(self, query: str) -> tuple[str, float]:
        """Determine best agent using A2A capability matching"""
        query_lower = query.lower().strip()
        best_agent = None
        best_confidence = 0.0

        for agent_id, spec in self.agent_specializations.items():
            # Calculate confidence based on keyword matching
            keyword_matches = sum(1 for keyword in spec["keywords"] if keyword in query_lower)
            confidence = min(keyword_matches / len(spec["keywords"]), 1.0)

            # Boost confidence for primary role match
            if confidence > 0:
                confidence = min(confidence * 1.2, 1.0)

            if confidence > best_confidence and confidence >= spec["confidence_threshold"]:
                best_agent = agent_id
                best_confidence = confidence

        # Default to greeting agent for low-confidence queries (better UX)
        if not best_agent or best_confidence < 0.3:
            best_agent = "greeting_agent"
            best_confidence = 0.5

        return best_agent, best_confidence

    def delegate_with_a2a(self, agent_id: str, query: str) -> Dict[str, Any]:
        """Delegate task using A2A protocol"""

        try:
            # First check agent health via A2A
            health_result = self.a2a.health_check_agent(agent_id)

            if "error" in health_result:
                return {
                    "error": f"Agent {agent_id} health check failed",
                    "details": health_result.get("error"),
                }

            # Delegate task via A2A protocol
            delegation_result = self.a2a.delegate_task(
                agent_id,
                query,
                context={
                    "source": "main_agent",
                    "protocol": "a2a",
                    "timestamp": self.a2a.create_message(
                        MessageType.TASK_REQUEST, agent_id, {}
                    ).timestamp,
                },
            )

            if "error" not in delegation_result:
                return {
                    "status": "success",
                    "result": delegation_result.get("payload", {}).get("result", "No response"),
                    "agent": agent_id,
                    "protocol": "a2a",
                    "delegation_id": delegation_result.get("correlation_id"),
                }
            else:
                return delegation_result

        except Exception as e:
            return {"error": "a2a_delegation_failed", "details": str(e), "fallback_available": True}

    def fallback_to_http(self, agent_id: str, query: str) -> Dict[str, Any]:
        """Fallback to direct HTTP communication"""

        if agent_id not in self.agent_endpoints:
            return {"error": f"Unknown agent: {agent_id}"}

        try:
            endpoint = self.agent_endpoints[agent_id]
            response = requests.post(
                f"{endpoint}/task",
                json={"input": query},
                headers={"Content-Type": "application/json"},
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "success",
                    "result": data.get("result", "No response"),
                    "agent": agent_id,
                    "protocol": "http_fallback",
                }
            else:
                return {"error": f"HTTP fallback failed: {response.status_code}"}

        except Exception as e:
            return {"error": f"HTTP fallback failed: {str(e)}"}

    def process_query_a2a(self, query: str) -> str:
        """Process query using A2A protocol with HTTP fallback"""

        # Determine best agent using A2A analysis
        best_agent, confidence = self.determine_best_agent_a2a(query)

        print(f"A2A routing '{query}' to {best_agent} (confidence: {confidence:.2f})")

        # Try A2A delegation first
        result = self.delegate_with_a2a(best_agent, query)

        # Fallback to HTTP if A2A fails
        if "error" in result and result.get("fallback_available"):
            print(f"WARNING: A2A delegation failed, falling back to HTTP...")
            result = self.fallback_to_http(best_agent, query)

        # Additional fallback to other agents
        if "error" in result and best_agent != "greeting_agent":
            print(f"WARNING: Primary agent failed, trying greeting agent...")
            fallback_result = self.fallback_to_http("greeting_agent", query)
            if "error" not in fallback_result:
                response = fallback_result.get("result", "No response")
                return f"Primary agent unavailable, but I can help!\n\n{response}\n\n_Fallback response from GreetingAgent_"

        if "error" in result:
            # Ultimate fallback with A2A system status
            a2a_status = self.a2a.get_protocol_status()

            return f"""I'm having trouble with the agent network right now.

**Your query:** "{query}"

**A2A Protocol Status:**
  Protocol Version: {a2a_status['protocol_version']}
  Known Agents: {a2a_status['known_agents']}
  Security: {'Enabled' if a2a_status['security_enabled'] else 'Disabled'}
  Pending Requests: {a2a_status['pending_requests']}

**Direct suggestions:**
  • For employee data: Try "list all employees" or "Engineering department"
  • For greetings: Try "hello" or "help"
  • For system info: Try "who are you"

**System Issue:** {result.get('error', 'Unknown error')}

Please try again, or check if all agent servers are running!"""

        # Success! Format response with A2A attribution
        response = result.get("result", "No response available")
        agent_name = result.get("agent", best_agent)
        protocol = result.get("protocol", "unknown")

        protocol_badge = "A2A" if protocol == "a2a" else "HTTP"

        return f"{response}\n\n_Response from {agent_name} via {protocol_badge} protocol_"

    def build_app(self, host: str, port: int) -> FastAPI:
        """Build and return the FastAPI app (for serving and tests)."""
        app = FastAPI(
            title=f"{self.name} A2A API", description="A2A-Enhanced Multi-Agent Coordinator"
        )
        base_url = f"http://{host}:{port}"

        # Feature flag: optionally mount official A2A SDK JSON-RPC server and agent card
        USE_A2A_SDK = os.getenv("USE_A2A_SDK", "false").lower() in {"1", "true", "yes"}

        if USE_A2A_SDK:
            sdk = _load_a2a_sdk_modules()

            AgentCard = sdk["types"].AgentCard
            AgentCapabilities = getattr(sdk["types"], "AgentCapabilities")
            AgentSkill = getattr(sdk["types"], "AgentSkill")

            # Coordinator exposes simple skills that describe routing capability
            skills = [
                AgentSkill(
                    id="routing",
                    name="routing",
                    description="Intelligent query routing to specialized agents",
                    tags=["coordination", "routing", "a2a"],
                    input_modes=["text"],
                    output_modes=["text"],
                ),
                AgentSkill(
                    id="discovery",
                    name="discovery",
                    description="A2A agent discovery and health monitoring",
                    tags=["discovery", "health"],
                    input_modes=["text"],
                    output_modes=["text"],
                ),
            ]

            card = AgentCard(
                name=self.name,
                description="Coordinator agent that routes queries to specialists",
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

            class MainAgentExecutor(AgentExecutorBase):
                def __init__(self, outer: "MainAgentA2A"):
                    self.outer = outer

                async def execute(self, context, event_queue) -> None:
                    text = get_message_text(context.message) if context.message else ""
                    reply = self.outer.process_query_a2a(text or "")
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
                agent_executor=MainAgentExecutor(self),
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
                result = self.process_query_a2a(request.input)
                return JSONResponse(
                    {
                        "status": "success",
                        "result": result,
                        "agent": self.name,
                        "role": "A2A Coordinator",
                        "protocol_version": "1.0",
                    }
                )
            except Exception as e:
                return JSONResponse(
                    {
                        "status": "error",
                        "error": str(e),
                        "agent": self.name,
                        "suggestion": "Try checking A2A protocol status at /a2a/status",
                    },
                    status_code=500,
                )

        if not USE_A2A_SDK:

            @app.post("/a2a")
            async def handle_a2a_message(request: Request):
                """Handle incoming A2A protocol messages (legacy)."""
                try:
                    message_data = await request.json()

                    # Add special handling for delegation requests
                    if message_data.get("message_type") == MessageType.DELEGATION_REQUEST.value:
                        # Extract task from A2A message
                        payload = message_data.get("payload", {})
                        task = payload.get("task", "")

                        if task:
                            # Process the delegated task
                            result = self.process_query_a2a(task)

                            # Create A2A response
                            response_message = self.a2a.create_message(
                                MessageType.DELEGATION_RESPONSE,
                                message_data.get("sender_id", "unknown"),
                                {
                                    "status": "success",
                                    "result": result,
                                    "processed_by": self.agent_id,
                                    "protocol": "a2a",
                                },
                                correlation_id=message_data.get("correlation_id"),
                            )

                            return JSONResponse(response_message.to_dict())

                    # Handle other A2A messages using protocol handler
                    response = self.a2a.handle_incoming_message(message_data)
                    return JSONResponse(response)

                except Exception as e:
                    return JSONResponse(
                        {"error": "a2a_message_processing_failed", "details": str(e)},
                        status_code=500,
                    )

        @app.get("/health")
        async def health_check():
            # Discover agents on health check
            try:
                discovered = self.discover_agents()
                agent_count = len(discovered)
            except:
                agent_count = 0

            return {
                "status": "healthy",
                "agent": self.name,
                "role": "A2A Multi-Agent Coordinator",
                "protocol_version": "1.0",
                "discovered_agents": agent_count,
                "a2a_status": self.a2a.get_protocol_status(),
            }

        @app.get("/a2a/status")
        async def a2a_status():
            """Get detailed A2A protocol status"""
            return self.a2a.get_protocol_status()

    # Legacy JSON-RPC path removed; official SDK serves JSON-RPC at POST /a2a

        if not USE_A2A_SDK:

            @app.get("/.well-known/agent-card.json")
            async def agent_card():
                return {
                    "agentId": self.agent_id,
                    "agentName": self.name,
                    "agentType": self.agent_type,
                    "a2a": {
                        "version": "1.0",
                        "transport": "jsonrpc-2.0",
                        "rpcUrl": f"{base_url}/a2a",
                    },
                    "endpoints": {
                        "health": f"{base_url}/health",
                        "task": f"{base_url}/task",
                        "status": f"{base_url}/a2a/status",
                        "discover": f"{base_url}/a2a/discover",
                    },
                }

            @app.get("/.well-known/agent.json")
            async def agent_json_alias():
                return await agent_card()

        @app.get("/a2a/discover")
        async def discover_agents_endpoint():
            """Trigger agent discovery"""
            try:
                discovered = self.discover_agents()
                return {
                    "status": "success",
                    "discovered_agents": len(discovered),
                    "agents": {
                        agent_id: {
                            "name": profile.agent_name,
                            "type": profile.agent_type,
                            "endpoint": profile.endpoint,
                            "capabilities": len(profile.capabilities),
                        }
                        for agent_id, profile in discovered.items()
                    },
                }
            except Exception as e:
                return JSONResponse({"status": "error", "error": str(e)}, status_code=500)

        @app.get("/")
        async def root():
            return {
                "agent": self.name,
                "role": "A2A Multi-Agent Coordinator",
                "description": "Enhanced coordinator with Agent-to-Agent protocol support",
                "capabilities": [
                    "A2A protocol communication",
                    "Intelligent query routing",
                    "Agent discovery and health monitoring",
                    "Secure message authentication",
                    "HTTP fallback support",
                ],
                "protocol_version": "1.0",
                "endpoints": {
                    "POST /task": "Process and route queries",
                    "POST /a2a": "A2A protocol message handling",
                    "GET /health": "Health check with A2A status",
                    "GET /a2a/status": "Detailed A2A protocol status",
                    "GET /a2a/discover": "Trigger agent discovery",
                    "GET /": "Coordinator information",
                },
            }

        return app

    def serve(self, host: str = "localhost", port: int = None):
        """Start A2A-enhanced HTTP server"""
        if port is None:
            port = self.port

        app = self.build_app(host, port)

        logger.info(
            "Starting %s (A2A-Enhanced Coordinator) on http://%s:%s",
            self.name,
            host,
            port,
        )
        logger.debug("A2A System Architecture:")
        logger.debug("  MainAgent - A2A coordination and routing")
        logger.debug(
            "  GreetingAgent - Social interaction (port %s)",
            os.getenv("GREETING_AGENT_PORT", "8003"),
        )
        logger.debug(
            "  HRAgent - Employee data and analytics (port %s)",
            os.getenv("HR_AGENT_PORT", "8002"),
        )
        logger.debug(
            "A2A Communication Flow: User → MainAgent → A2A Protocol → Specialized Agent → MCP Server → Database"
        )
        logger.debug(
            "A2A Features: Message authentication with HMAC signatures, Automatic agent discovery, Health monitoring and status tracking, HTTP fallback for compatibility"
        )

        # Cleanup periodic expired requests
        import threading
        import time

        def cleanup_thread():
            while True:
                time.sleep(60)  # Clean up every minute
                self.a2a.cleanup_expired_requests()

        cleanup_worker = threading.Thread(target=cleanup_thread, daemon=True)
        cleanup_worker.start()

        uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    logger.info("A2A-Enhanced MainAgent - Advanced Multi-Agent Coordinator")
    logger.info("%s", "=" * 60)
    logger.info("Phase 6 Capabilities:")
    logger.info("  Agent-to-Agent (A2A) protocol implementation")
    logger.info("  Secure message authentication and verification")
    logger.info("  Automatic agent discovery and registration")
    logger.info("  Advanced health monitoring and status tracking")
    logger.info("  HTTP fallback for legacy compatibility")
    logger.info("  Intelligent query routing with confidence scoring")
    # Instantiate and serve

    main_agent_a2a = MainAgentA2A()

    # Start the A2A-enhanced coordinating agent
    host = os.getenv("MAIN_AGENT_HOST", "localhost")
    port = int(os.getenv("MAIN_AGENT_PORT", "8001"))

    main_agent_a2a.serve(host=host, port=port)
