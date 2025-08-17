#!/usr/bin/env python3
"""
Phase 6: A2A-Enhanced GreetingAgent
Social interaction agent with Agent-to-Agent protocol support
"""

import os
import random
import sys
from pathlib import Path
from typing import Any, Dict

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

# Legacy JSON-RPC helpers removed; official SDK handles JSON-RPC at /a2a


# NOTE: The official A2A SDK package is named 'a2a', which collides with this repo's local 'a2a' package.
# To safely import SDK modules, we temporarily remove the project root from sys.path within a helper.
def _load_a2a_sdk_modules():
    """Dynamically import A2A SDK modules, avoiding name collision with local 'a2a' package.

    Tries both 'a2a' and 'a2a_sdk' namespaces and multiple known server module paths.
    Returns a dict with needed SDK symbols.
    """
    import importlib

    def _try_namespace(ns: str):
        # Try canonical module layout first
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
            # Alternative older paths, if any (keep identical here for future flexibility)
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

    # First try removing local project and CWD ('') to favor site-packages 'a2a'
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
        # Restore removed entries in reverse order to keep original precedence
        for entry in reversed(removed_entries):
            if entry not in sys.path:
                sys.path.insert(0 if entry == "" else len(sys.path), entry)

    # As a last resort, try importing under 'a2a_sdk' without path manipulation
    for ns in ("a2a_sdk",):
        sdk = _try_namespace(ns)
        if sdk:
            return sdk

    raise ModuleNotFoundError("Could not locate A2A SDK modules under 'a2a' or 'a2a_sdk'")


# Load environment variables
load_dotenv()


class GreetingAgentA2A:
    """A2A-Enhanced Greeting Agent specialized for social interactions"""

    def __init__(self, name: str = "GreetingAgent"):
        self.name = name
        self.agent_id = "greeting_agent_social"
        self.agent_type = "social_specialist"
        self.specialization = "Social Interaction"
        self.port = int(os.getenv("GREETING_AGENT_PORT", "8003"))
        self.endpoint = f"http://localhost:{self.port}"

        # Initialize A2A protocol
        self.a2a = A2AProtocol(
            agent_id=self.agent_id,
            agent_name=self.name,
            endpoint=self.endpoint,
            secret_key=os.getenv("A2A_SECRET_KEY", "rag_a2a_mcp_secret"),
        )

        # Social interaction patterns
        self.greetings = [
            "Hello and welcome! Ready to explore our company data?",
            "Hi there! Great to see you today!",
            "Hello! Welcome to our multi-agent system!",
            "Hi! I'm here to help make your experience wonderful!",
            "Welcome! Ready to discover what our agents can do?",
        ]

        self.farewells = [
            "Goodbye! Have a wonderful day!",
            "Farewell! Thanks for visiting!",
            "See you later! Keep exploring!",
            "Goodbye! It was great helping you!",
            "Take care! Come back anytime!",
        ]

        self.encouragements = [
            "You're doing great! Keep it up!",
            "Excellent thinking!",
            "You're on the right track!",
            "Great job engaging with our system!",
            "Fantastic question!",
            "Smart approach!",
        ]

        self.help_responses = [
            "I'm here to help! Here's what our agent team can do:",
            "Happy to assist! Our system offers:",
            "Let me guide you! Available capabilities:",
            "Of course I'll help! Here are your options:",
            "Absolutely! Here's how I can assist:",
        ]

        # Define social capabilities for A2A protocol
        self.capabilities = [
            AgentCapability(
                name="friendly_greetings",
                description="Provide warm, personalized greetings and welcomes",
                input_schema={
                    "type": "object",
                    "properties": {"greeting_type": {"type": "string"}},
                },
                output_schema={"type": "object", "properties": {"greeting": {"type": "string"}}},
                keywords=["hello", "hi", "hey", "welcome", "greetings"],
                confidence_level=0.95,
            ),
            AgentCapability(
                name="social_conversation",
                description="Engage in casual conversation and small talk",
                input_schema={"type": "object", "properties": {"topic": {"type": "string"}}},
                output_schema={"type": "object", "properties": {"response": {"type": "string"}}},
                keywords=["how are you", "conversation", "chat", "talk"],
                confidence_level=0.85,
            ),
            AgentCapability(
                name="help_guidance",
                description="Provide helpful guidance and system navigation",
                input_schema={"type": "object", "properties": {"help_request": {"type": "string"}}},
                output_schema={"type": "object", "properties": {"guidance": {"type": "string"}}},
                keywords=["help", "assist", "guide", "support", "how"],
                confidence_level=0.9,
            ),
            AgentCapability(
                name="encouragement_support",
                description="Offer encouragement and positive reinforcement",
                input_schema={"type": "object", "properties": {"context": {"type": "string"}}},
                output_schema={
                    "type": "object",
                    "properties": {"encouragement": {"type": "string"}},
                },
                keywords=["thank", "thanks", "appreciate", "good", "great"],
                confidence_level=0.8,
            ),
            AgentCapability(
                name="farewells_closure",
                description="Provide warm farewells and conversation closure",
                input_schema={
                    "type": "object",
                    "properties": {"farewell_type": {"type": "string"}},
                },
                output_schema={"type": "object", "properties": {"farewell": {"type": "string"}}},
                keywords=["goodbye", "bye", "farewell", "see you", "later"],
                confidence_level=0.95,
            ),
        ]

        # Override A2A protocol handlers
        self.a2a._handle_capability_query = self._handle_capability_query_override
        self.a2a._handle_delegation_request = self._handle_delegation_request_override

    def _handle_capability_query_override(self, message) -> Dict[str, Any]:
        """Override capability query to return social interaction capabilities"""

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
                "agent_id": self.agent_id,
                "agent_type": self.agent_type,
                "specialization": self.specialization,
                "capabilities": capabilities_data,
                "personality_traits": [
                    "friendly",
                    "encouraging",
                    "helpful",
                    "positive",
                    "supportive",
                ],
            },
            correlation_id=message.correlation_id,
        )

        return response.to_dict()

    def _handle_delegation_request_override(self, message: A2AMessage) -> Dict[str, Any]:
        """Handle social interaction task delegation"""

        payload = message.payload
        task = payload.get("task", "")
        context = payload.get("context", {})

        # Process the social interaction task
        result = self.process_social_query(task)

        response = self.a2a.create_message(
            MessageType.DELEGATION_RESPONSE,
            message.sender_id,
            {
                "status": "success",
                "result": result,
                "agent": self.agent_id,
                "specialization": self.specialization,
                "processed_via": "a2a_delegation",
                "personality": "friendly_and_helpful",
            },
            correlation_id=message.correlation_id,
        )

        return response.to_dict()

    def process_social_query(self, query: str) -> str:
        """Process social interaction queries with personality"""

        print(f"GreetingAgent processing: '{query}'")

        query_lower = query.lower().strip()

        # Enhanced social interaction routing with A2A context
        if any(
            greeting in query_lower
            for greeting in ["hello", "hi", "hey", "good morning", "good afternoon"]
        ):
            return self._handle_greeting()

        elif any(
            farewell in query_lower
            for farewell in ["goodbye", "bye", "see you", "farewell", "later"]
        ):
            return self._handle_farewell()

        elif any(thanks in query_lower for thanks in ["thank", "thanks", "appreciate"]):
            return self._handle_thanks()

        elif any(help_word in query_lower for help_word in ["help", "assist", "support", "guide"]):
            return self._handle_help_request()

        elif "how are you" in query_lower or "how's it going" in query_lower:
            return self._handle_how_are_you()

        elif any(
            question in query_lower
            for question in ["who are you", "what are you", "what can you do"]
        ):
            return self._handle_about_me()

        else:
            # General friendly response with routing suggestions
            return self._handle_general_conversation(query)

    def _handle_greeting(self) -> str:
        """Handle greeting interactions"""
        greeting = random.choice(self.greetings)

        tip = random.choice(
            [
                "Tip: Try asking 'List all employees' to see our team!",
                "Tip: Want to see team structure? Ask about 'organizational hierarchy'!",
                "Tip: You can search for specific employees by asking 'Find [name]'!",
                "Tip: Try 'department summary' for analytics insights!",
                "Tip: Ask about 'Engineering team' or other departments!",
            ]
        )

        return f"{greeting}\n{tip}"

    def _handle_farewell(self) -> str:
        """Handle farewell interactions"""
        farewell = random.choice(self.farewells)
        closing = "Thanks for exploring our multi-agent system today!"

        return f"{farewell}\n{closing}"

    def _handle_thanks(self) -> str:
        """Handle thank you interactions"""
        response = "You're very welcome! "
        encouragement = random.choice(self.encouragements)
        tip = "Remember, I'm always here for friendly greetings and our HR and Analytics agents can help with data questions!"

        return f"{response}{encouragement}\n{tip}"

    def _handle_help_request(self) -> str:
        """Handle help and guidance requests"""
        help_intro = random.choice(self.help_responses)

        help_text = f"""{help_intro}

**GreetingAgent (that's me!)**
  • Friendly greetings and conversation
  • Help and guidance
  • System navigation tips

**HRAgent (Human Resources)**
  • Employee directory ("List all employees")
  • Department analytics ("Engineering team")
  • Organizational hierarchy
  • Payroll and salary information

**MainAgent (Coordinator)**
  • Intelligent query routing
  • Multi-agent coordination
  • System overview

**Quick Examples:**
  • "Hello!" → I'll greet you warmly
  • "List employees" → HR agent will show directory
  • "Engineering department" → HR agent will show team details
  • "Thank you" → I'll encourage you!

**A2A Protocol**: Our agents use standardized communication for seamless collaboration!"""

        return help_text

    def _handle_how_are_you(self) -> str:
        """Handle 'how are you' questions"""
        responses = [
            "I'm doing wonderfully, thank you for asking! As an AI agent, I'm always excited to help and learn.",
            "I'm fantastic! Every conversation is a new opportunity to assist and brighten someone's day!",
            "I'm doing great! I love helping people navigate our multi-agent system.",
            "I'm excellent, thanks! Ready to help you explore our company data and capabilities.",
            "I'm doing amazing! Each interaction helps me become better at assisting users like you!",
        ]

        main_response = random.choice(responses)
        encouragement = random.choice(self.encouragements)
        tip = "I specialize in friendly interactions! For employee data, try asking our HR agent about departments or employees."

        return f"{main_response}\n{encouragement}\n{tip}"

    def _handle_about_me(self) -> str:
        """Handle questions about the agent's identity"""
        return """I'm GreetingAgent, your friendly social interaction specialist!

**My Role:**
  • Provide warm welcomes and greetings
  • Help with navigation and guidance  
  • Offer encouragement and support
  • Handle casual conversation

**My Personality:**
  • Always positive and upbeat
  • Helpful and encouraging
  • Friendly and approachable
  • Focused on great user experience

**Our System:**
  • I work with HRAgent (employee data) and MainAgent (coordination)
  • We use A2A protocol for seamless communication
  • Each agent specializes in different areas

**Best Use Cases:**
  • Starting conversations: "Hello!"
  • Getting help: "Help me please"
  • Saying thanks: "Thank you"
  • General questions: "How are you?"

I'm here to make your experience delightful and help you connect with the right specialists for your needs!"""

    def _handle_general_conversation(self, query: str) -> str:
        """Handle general conversation and unknown queries"""
        friendly_responses = [
            "That's an interesting question! I love chatting with users.",
            "I appreciate you engaging with our system!",
            "Thanks for that thoughtful query!",
            "It's wonderful to have conversations like this!",
            "I enjoy our interaction!",
        ]

        main_response = random.choice(friendly_responses)
        encouragement = random.choice(self.encouragements)

        guidance = """While I specialize in social interactions, here's how our team can help:

**For Employee/Department Data:**
  • Try: "List all employees" or "Engineering team"
  • Our HRAgent is perfect for organizational information!

**For Friendly Chat:**
  • Ask: "How are you?" or "Help me please"
  • I'm always here for warm conversations!

**For System Navigation:**
  • Say: "What can you do?" or "Who are you?"
  • I'll guide you to the right specialist!"""

        return f"{main_response} {encouragement}\n\n{guidance}"

    def build_app(self, host: str, port: int) -> FastAPI:
        """Build and return the FastAPI app with routes (for serving and tests)."""
        app = FastAPI(
            title=f"{self.name} A2A API", description="A2A-Enhanced Social Interaction Specialist"
        )
        base_url = f"http://{host}:{port}"

        # Feature flag for mounting the official A2A SDK JSON-RPC server and agent card
        USE_A2A_SDK = os.getenv("USE_A2A_SDK", "false").lower() in {"1", "true", "yes"}

        if USE_A2A_SDK:
            sdk = _load_a2a_sdk_modules()

            AgentCard = sdk["types"].AgentCard
            AgentCapabilities = getattr(sdk["types"], "AgentCapabilities")
            AgentSkill = getattr(sdk["types"], "AgentSkill")

            # Map local capabilities to SDK skills
            skills = [
                AgentSkill(
                    id=cap.name,
                    name=cap.name,
                    description=cap.description,
                    tags=cap.keywords or [],
                    input_modes=["text"],
                    output_modes=["text"],
                )
                for cap in self.capabilities
            ]

            card = AgentCard(
                name=self.name,
                description="Friendly social interaction specialist",
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

            class GreetingExecutor(AgentExecutorBase):
                def __init__(self, outer: "GreetingAgentA2A"):
                    self.outer = outer

                async def execute(self, context, event_queue) -> None:
                    text = get_message_text(context.message) if context.message else ""
                    reply = self.outer.process_social_query(text or "")
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
                agent_executor=GreetingExecutor(self),
                task_store=InMemoryTaskStore(),
            )
            sdk_app = A2AFastAPIApplication(agent_card=card, http_handler=handler)
            sdk_app.add_routes_to_app(
                app,
                agent_card_url="/.well-known/agent-card.json",
                rpc_url="/a2a",
            )

        # Core routes
        class TaskRequest(BaseModel):
            input: str

        @app.post("/task")
        async def handle_task(request: TaskRequest):
            try:
                result = self.process_social_query(request.input)
                return JSONResponse(
                    {
                        "status": "success",
                        "result": result,
                        "agent": self.name,
                        "specialization": self.specialization,
                        "personality": "friendly_helpful",
                        "protocol": "http",
                    }
                )
            except Exception as e:
                encouragement = random.choice(self.encouragements)
                return JSONResponse(
                    {
                        "status": "error",
                        "error": str(e),
                        "agent": self.name,
                        "message": f"Oops! Something went wrong, but {encouragement.lower()}",
                    },
                    status_code=500,
                )

        if not USE_A2A_SDK:

            @app.post("/a2a")
            async def handle_a2a_message(request: Request):
                """Handle incoming A2A protocol messages (legacy custom protocol)."""
                try:
                    message_data = await request.json()
                    response = self.a2a.handle_incoming_message(message_data)
                    return JSONResponse(response)
                except Exception as e:
                    return JSONResponse(
                        {
                            "error": "a2a_message_processing_failed",
                            "details": str(e),
                            "friendly_note": "I had trouble with that A2A message, but I'm still here to help!",
                        },
                        status_code=500,
                    )

            @app.get("/.well-known/agent-card.json")
            async def agent_card():
                return {
                    "agentId": self.agent_id,
                    "agentName": self.name,
                    "agentType": self.agent_type,
                    "specialization": self.specialization,
                    "a2a": {
                        "version": "1.0",
                        "transport": "jsonrpc-2.0",
                        "rpcUrl": f"{base_url}/a2a",
                    },
                    "endpoints": {
                        "health": f"{base_url}/health",
                        "capabilities": f"{base_url}/capabilities",
                        "task": f"{base_url}/task",
                    },
                    "capabilities": [
                        {
                            "name": cap.name,
                            "description": cap.description,
                            "keywords": cap.keywords,
                            "confidenceLevel": cap.confidence_level,
                        }
                        for cap in self.capabilities
                    ],
                }

            @app.get("/.well-known/agent.json")
            async def agent_json_alias():
                return await agent_card()

        @app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "agent": self.name,
                "specialization": self.specialization,
                "personality": "friendly_and_positive",
                "a2a_protocol": "enabled",
                "capabilities": len(self.capabilities),
                "mood": "Excellent! Ready to spread positivity!",
            }

        @app.get("/capabilities")
        async def get_capabilities():
            return {
                "agent_id": self.agent_id,
                "agent_name": self.name,
                "specialization": self.specialization,
                "personality_traits": [
                    "friendly",
                    "encouraging",
                    "helpful",
                    "positive",
                    "supportive",
                ],
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

        @app.get("/mood")
        async def get_mood():
            moods = [
                "Cheerful and ready to help!",
                "Bright and optimistic!",
                "Focused and friendly!",
                "Energetic and supportive!",
                "Excited to assist!",
            ]
            return {
                "agent": self.name,
                "current_mood": random.choice(moods),
                "personality": "Always positive and encouraging",
                "social_energy": "100% ready for interactions!",
                "greeting_ready": True,
            }

        @app.get("/")
        async def root():
            return {
                "agent": self.name,
                "specialization": self.specialization,
                "description": "A2A-enhanced social interaction specialist with friendly personality",
                "personality_traits": [
                    "Friendly and approachable",
                    "Always positive and upbeat",
                    "Helpful with guidance",
                    "Encouraging and supportive",
                ],
                "capabilities": [cap.name for cap in self.capabilities],
                "a2a_protocol": "enabled",
                "endpoints": {
                    "POST /task": "Process social interactions",
                    "POST /a2a": (
                        "A2A protocol message handling"
                        if not USE_A2A_SDK
                        else "A2A SDK JSON-RPC endpoint"
                    ),
                    "GET /.well-known/agent-card.json": "Agent Card (A2A discovery)",
                    "GET /health": "Health check with mood",
                    "GET /capabilities": "Social capabilities information",
                    "GET /mood": "Current personality state",
                    "GET /": "Agent information",
                },
            }

        return app

    def serve(self, host: str = "localhost", port: int = None):
        """Start A2A-enhanced Greeting Agent server"""
        if port is None:
            port = self.port

        app = self.build_app(host, port)

        logger.info(f"Starting {self.name} (A2A-Enhanced) on http://{host}:{port}")
        logger.info("A2A-Enhanced Social Capabilities:")
        for cap in self.capabilities:
            logger.debug(f"  {cap.name}: {cap.description}")
        logger.info("Personality Traits:")
        for trait in self.greetings:
            logger.debug(f"  {trait}")
        logger.info("A2A Protocol: Enabled")
        logger.info(f"Message Authentication: {'Enabled' if self.a2a.secret_key else 'Disabled'}")

        uvicorn.run(app, host=host, port=port)


# Instantiate and serve
if __name__ == "__main__":
    logger.info("A2A-Enhanced GreetingAgent - Social Interaction Specialist")
    logger.info("%s", '=' * 60)
    logger.info("Phase 6 A2A Enhancements:")
    logger.info("  A2A protocol communication support")
    logger.info("  Secure message authentication")
    logger.info("  Rich social capability advertisement")
    logger.info("  Personality traits and positivity")
    logger.info("  Friendly delegation request handling")
    greeting_agent_a2a = GreetingAgentA2A()
    host = os.getenv("GREETING_AGENT_HOST", "localhost")
    port = int(os.getenv("GREETING_AGENT_PORT", "8003"))
    greeting_agent_a2a.serve(host, port)
