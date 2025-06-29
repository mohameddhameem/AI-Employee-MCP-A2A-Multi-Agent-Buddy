#!/usr/bin/env python3
"""
Phase 6: A2A-Enhanced MainAgent 
MainAgent with Agent-to-Agent protocol integration for standardized communication
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
import requests
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from a2a.protocol import A2AProtocol, MessageType, AgentProfile, AgentCapability

# Load environment variables
load_dotenv()

class MainAgentA2A:
    """Enhanced MainAgent with A2A protocol support"""
    
    def __init__(self, name: str = "MainAgent"):
        self.name = name
        self.agent_id = "main_agent_coordinator"
        self.agent_type = "coordinator"
        self.port = int(os.getenv('MAIN_AGENT_PORT', '8001'))
        self.endpoint = f"http://localhost:{self.port}"
        
        # Initialize A2A protocol
        self.a2a = A2AProtocol(
            agent_id=self.agent_id,
            agent_name=self.name, 
            endpoint=self.endpoint,
            secret_key=os.getenv('A2A_SECRET_KEY', 'rag_a2a_mcp_secret')
        )
        
        # Agent registry with A2A capabilities
        self.agent_endpoints = {
            "greeting_agent": f"http://localhost:{os.getenv('GREETING_AGENT_PORT', '8003')}",
            "hr_agent": f"http://localhost:{os.getenv('HR_AGENT_PORT', '8002')}"
        }
        
        # Enhanced agent specializations
        self.agent_specializations = {
            "greeting_agent": {
                "keywords": ["hello", "hi", "hey", "goodbye", "bye", "thank", "help", "who are you", "how are you"],
                "confidence_threshold": 0.8,
                "primary_role": "social_interaction"
            },
            "hr_agent": {
                "keywords": ["employee", "department", "salary", "payroll", "hierarchy", "team", "staff", "manager", "organization"],
                "confidence_threshold": 0.9,
                "primary_role": "data_specialist"
            }
        }
        
        # MCP server endpoint for direct fallback
        self.mcp_url = f"http://localhost:{os.getenv('MCP_SERVER_PORT', '8000')}/mcp"
        
    def discover_agents(self) -> Dict[str, AgentProfile]:
        """Discover agents using A2A protocol"""
        print("🔍 Discovering agents using A2A protocol...")
        
        broadcast_endpoints = list(self.agent_endpoints.values())
        discovered_agents = self.a2a.discover_agents(broadcast_endpoints)
        
        print(f"✅ Discovered {len(discovered_agents)} agents via A2A protocol")
        
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
                    "details": health_result.get("error")
                }
            
            # Delegate task via A2A protocol
            delegation_result = self.a2a.delegate_task(
                agent_id,
                query,
                context={
                    "source": "main_agent",
                    "protocol": "a2a",
                    "timestamp": self.a2a.create_message(MessageType.TASK_REQUEST, agent_id, {}).timestamp
                }
            )
            
            if "error" not in delegation_result:
                return {
                    "status": "success",
                    "result": delegation_result.get("payload", {}).get("result", "No response"),
                    "agent": agent_id,
                    "protocol": "a2a",
                    "delegation_id": delegation_result.get("correlation_id")
                }
            else:
                return delegation_result
                
        except Exception as e:
            return {
                "error": "a2a_delegation_failed",
                "details": str(e),
                "fallback_available": True
            }
    
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
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "success",
                    "result": data.get("result", "No response"),
                    "agent": agent_id,
                    "protocol": "http_fallback"
                }
            else:
                return {"error": f"HTTP fallback failed: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"HTTP fallback failed: {str(e)}"}
    
    def process_query_a2a(self, query: str) -> str:
        """Process query using A2A protocol with HTTP fallback"""
        
        # Determine best agent using A2A analysis
        best_agent, confidence = self.determine_best_agent_a2a(query)
        
        print(f"🎯 A2A routing '{query}' to {best_agent} (confidence: {confidence:.2f})")
        
        # Try A2A delegation first
        result = self.delegate_with_a2a(best_agent, query)
        
        # Fallback to HTTP if A2A fails
        if "error" in result and result.get("fallback_available"):
            print(f"⚠️  A2A delegation failed, falling back to HTTP...")
            result = self.fallback_to_http(best_agent, query)
        
        # Additional fallback to other agents
        if "error" in result and best_agent != "greeting_agent":
            print(f"⚠️  Primary agent failed, trying greeting agent...")
            fallback_result = self.fallback_to_http("greeting_agent", query)
            if "error" not in fallback_result:
                response = fallback_result.get('result', 'No response')
                return f"🔄 Primary agent unavailable, but I can help!\n\n{response}\n\n🤖 _Fallback response from GreetingAgent_"
        
        if "error" in result:
            # Ultimate fallback with A2A system status
            a2a_status = self.a2a.get_protocol_status()
            
            return f"""🤔 I'm having trouble with the agent network right now.

**Your query:** "{query}"

🏥 **A2A Protocol Status:**
  📡 Protocol Version: {a2a_status['protocol_version']}
  🤖 Known Agents: {a2a_status['known_agents']}
  🔒 Security: {'Enabled' if a2a_status['security_enabled'] else 'Disabled'}
  ⏳ Pending Requests: {a2a_status['pending_requests']}

💡 **Direct suggestions:**
  • For employee data: Try "list all employees" or "Engineering department"
  • For greetings: Try "hello" or "help"
  • For system info: Try "who are you"

🔧 **System Issue:** {result.get('error', 'Unknown error')}

Please try again, or check if all agent servers are running!"""
        
        # Success! Format response with A2A attribution
        response = result.get('result', 'No response available')
        agent_name = result.get('agent', best_agent)
        protocol = result.get('protocol', 'unknown')
        
        protocol_badge = "🔗 A2A" if protocol == "a2a" else "📡 HTTP"
        
        return f"{response}\n\n🤖 _Response from {agent_name} via {protocol_badge} protocol_"
    
    def serve(self, host: str = "localhost", port: int = None):
        """Start A2A-enhanced HTTP server"""
        
        if port is None:
            port = self.port
        
        app = FastAPI(title=f"{self.name} A2A API", description="A2A-Enhanced Multi-Agent Coordinator")
        
        class TaskRequest(BaseModel):
            input: str
        
        @app.post("/task")
        async def handle_task(request: TaskRequest):
            try:
                result = self.process_query_a2a(request.input)
                return JSONResponse({
                    "status": "success",
                    "result": result,
                    "agent": self.name,
                    "role": "A2A Coordinator",
                    "protocol_version": "1.0"
                })
            except Exception as e:
                return JSONResponse({
                    "status": "error",
                    "error": str(e),
                    "agent": self.name,
                    "suggestion": "Try checking A2A protocol status at /a2a/status"
                }, status_code=500)
        
        @app.post("/a2a")
        async def handle_a2a_message(request: Request):
            """Handle incoming A2A protocol messages"""
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
                                "protocol": "a2a"
                            },
                            correlation_id=message_data.get("correlation_id")
                        )
                        
                        return JSONResponse(response_message.to_dict())
                
                # Handle other A2A messages using protocol handler
                response = self.a2a.handle_incoming_message(message_data)
                return JSONResponse(response)
                
            except Exception as e:
                return JSONResponse({
                    "error": "a2a_message_processing_failed",
                    "details": str(e)
                }, status_code=500)
        
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
                "a2a_status": self.a2a.get_protocol_status()
            }
        
        @app.get("/a2a/status")
        async def a2a_status():
            """Get detailed A2A protocol status"""
            return self.a2a.get_protocol_status()
        
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
                            "capabilities": len(profile.capabilities)
                        }
                        for agent_id, profile in discovered.items()
                    }
                }
            except Exception as e:
                return JSONResponse({
                    "status": "error",
                    "error": str(e)
                }, status_code=500)
        
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
                    "HTTP fallback support"
                ],
                "protocol_version": "1.0",
                "endpoints": {
                    "POST /task": "Process and route queries",
                    "POST /a2a": "A2A protocol message handling",
                    "GET /health": "Health check with A2A status",
                    "GET /a2a/status": "Detailed A2A protocol status",
                    "GET /a2a/discover": "Trigger agent discovery",
                    "GET /": "Coordinator information"
                }
            }
        
        print(f"🎯 Starting {self.name} (A2A-Enhanced Coordinator) on http://{host}:{port}")
        print("🏛️ A2A System Architecture:")
        print("  🎯 MainAgent - A2A coordination and routing")
        print(f"  😊 GreetingAgent - Social interaction (port {os.getenv('GREETING_AGENT_PORT', '8003')})")
        print(f"  🏢 HRAgent - Employee data and analytics (port {os.getenv('HR_AGENT_PORT', '8002')})")
        print()
        print("🔗 A2A Communication Flow:")
        print("  User → MainAgent → A2A Protocol → Specialized Agent → MCP Server → Database")
        print()
        print("📡 A2A Features:")
        print("  🔐 Message authentication with HMAC signatures")
        print("  🔍 Automatic agent discovery")
        print("  🏥 Health monitoring and status tracking")
        print("  📡 HTTP fallback for compatibility")
        print()
        
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

# Create the A2A-enhanced main agent
if __name__ == "__main__":
    print("🎯 A2A-Enhanced MainAgent - Advanced Multi-Agent Coordinator")
    print("=" * 60)
    print("🏛️ Phase 6 Capabilities:")
    print("  🔗 Agent-to-Agent (A2A) protocol implementation")
    print("  🔐 Secure message authentication and verification")
    print("  🔍 Automatic agent discovery and registration")
    print("  🏥 Advanced health monitoring and status tracking")
    print("  📡 HTTP fallback for legacy compatibility")
    print("  ⚡ Intelligent query routing with confidence scoring")
    print()
    
    main_agent_a2a = MainAgentA2A()
    
    # Start the A2A-enhanced coordinating agent
    host = os.getenv("MAIN_AGENT_HOST", "localhost") 
    port = int(os.getenv("MAIN_AGENT_PORT", "8001"))
    
    main_agent_a2a.serve(host=host, port=port)
