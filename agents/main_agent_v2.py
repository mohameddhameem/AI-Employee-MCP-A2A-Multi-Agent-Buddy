#!/usr/bin/env python3
"""
Phase 5: Enhanced MainAgent with Multi-Agent Delegation
Coordinates between specialized agents using agent-to-agent communication
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
import requests
from typing import Dict, Any, Optional

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Load environment variables
load_dotenv()

class MainAgent:
    """Coordinating agent that delegates to specialized agents"""
    
    def __init__(self, name: str = "MainAgent"):
        self.name = name
        
        # Agent registry with their specializations
        self.agents = {
            "greeting": {
                "url": f"http://localhost:{os.getenv('GREETING_AGENT_PORT', '8003')}",
                "specialization": "Social interaction, greetings, farewells, help",
                "keywords": ["hello", "hi", "hey", "goodbye", "bye", "thank", "help", "who are you", "how are you"]
            },
            "hr": {
                "url": f"http://localhost:{os.getenv('HR_AGENT_PORT', '8002')}",
                "specialization": "Employee data, departments, organizational hierarchy, payroll",
                "keywords": ["employee", "department", "salary", "payroll", "hierarchy", "team", "staff", "manager", "organization"]
            }
        }
        
        # Direct MCP integration for fallback
        self.mcp_url = f"http://localhost:{os.getenv('MCP_SERVER_PORT', '8000')}/mcp"
    
    def delegate_to_agent(self, agent_name: str, query: str) -> Dict[str, Any]:
        """Delegate query to a specialized agent"""
        if agent_name not in self.agents:
            return {"error": f"Unknown agent: {agent_name}"}
        
        agent_info = self.agents[agent_name]
        
        try:
            # Send query to specialized agent
            response = requests.post(
                f"{agent_info['url']}/task",
                json={"input": query},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Agent {agent_name} returned status {response.status_code}"}
                
        except requests.exceptions.ConnectionError:
            return {"error": f"Agent {agent_name} is not available (connection refused)"}
        except Exception as e:
            return {"error": f"Failed to contact {agent_name}: {str(e)}"}
    
    def determine_best_agent(self, query: str) -> str:
        """Determine which agent should handle the query"""
        query_lower = query.lower().strip()
        
        # Check for greeting patterns first (highest priority for user experience)
        greeting_keywords = self.agents["greeting"]["keywords"]
        if any(keyword in query_lower for keyword in greeting_keywords):
            return "greeting"
        
        # Check for HR patterns
        hr_keywords = self.agents["hr"]["keywords"] 
        if any(keyword in query_lower for keyword in hr_keywords):
            return "hr"
        
        # Default to greeting agent for unknown queries (better UX)
        return "greeting"
    
    def process_query(self, query: str) -> str:
        """Process query with intelligent agent delegation"""
        
        # Determine the best agent for this query
        best_agent = self.determine_best_agent(query)
        
        print(f"🎯 MainAgent routing '{query}' to {best_agent} agent")
        
        # Delegate to the chosen agent
        result = self.delegate_to_agent(best_agent, query)
        
        if "error" in result:
            # Fallback: try other agents or provide helpful response
            if best_agent != "greeting":
                print(f"⚠️  {best_agent} agent failed, trying greeting agent...")
                fallback_result = self.delegate_to_agent("greeting", query)
                if "error" not in fallback_result:
                    return f"🔄 Primary agent unavailable, but I can help!\n\n{fallback_result.get('result', 'No response')}"
            
            # Ultimate fallback
            return f"""🤔 I'm having trouble with my specialized agents right now.

**Your query:** "{query}"

🏥 **Agent Status Check:**
{self._get_agent_status()}

💡 **Direct suggestions:**
  • For employee data: Try "list all employees" or "Engineering department"
  • For greetings: Try "hello" or "help"
  • For system info: Try "who are you"

🔧 **System Issue:** {result.get('error', 'Unknown error')}

Please try again, or check if all agent servers are running!"""
        
        # Success! Return the result with agent attribution
        agent_name = result.get('agent', best_agent)
        specialization = result.get('specialization', 'Unknown')
        response = result.get('result', 'No response available')
        
        return f"{response}\n\n🤖 _Response from {agent_name} ({specialization})_"
    
    def _get_agent_status(self) -> str:
        """Check status of all registered agents"""
        status_report = ""
        
        for agent_name, agent_info in self.agents.items():
            try:
                health_response = requests.get(f"{agent_info['url']}/health", timeout=5)
                if health_response.status_code == 200:
                    status_report += f"  ✅ {agent_name.title()}Agent: Online\n"
                else:
                    status_report += f"  ❌ {agent_name.title()}Agent: HTTP {health_response.status_code}\n"
            except:
                status_report += f"  ❌ {agent_name.title()}Agent: Offline\n"
        
        return status_report
    
    def get_system_overview(self) -> str:
        """Get overview of the multi-agent system"""
        overview = "🏛️ Multi-Agent System Overview\n"
        overview += "=" * 40 + "\n\n"
        
        overview += f"🎯 **MainAgent (Coordinator)**\n"
        overview += f"  • Query analysis and routing\n"
        overview += f"  • Agent delegation and coordination\n"
        overview += f"  • Fallback handling\n\n"
        
        for agent_name, agent_info in self.agents.items():
            overview += f"🤖 **{agent_name.title()}Agent**\n"
            overview += f"  • Specialization: {agent_info['specialization']}\n"
            overview += f"  • Endpoint: {agent_info['url']}\n"
            overview += f"  • Keywords: {', '.join(agent_info['keywords'][:5])}...\n\n"
        
        overview += "🔧 **System Architecture:**\n"
        overview += "```\n"
        overview += "User Query → MainAgent → Specialized Agent → MCP Server → Database\n"
        overview += "     ↓           ↓              ↓              ↓\n"
        overview += "  Analysis → Delegation → Processing → Data Retrieval\n"
        overview += "```\n\n"
        
        overview += f"📊 **Current Status:**\n{self._get_agent_status()}"
        
        return overview
    
    def serve(self, host: str = "localhost", port: int = 8001):
        """Start HTTP server for the main coordinating agent"""
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        from pydantic import BaseModel
        import uvicorn
        
        app = FastAPI(title=f"{self.name} API", description="Multi-Agent Coordinator")
        
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
                    "role": "Coordinator",
                    "system": "Multi-Agent"
                })
            except Exception as e:
                return JSONResponse({
                    "status": "error",
                    "error": str(e),
                    "agent": self.name,
                    "suggestion": "Try checking if specialized agents are running"
                }, status_code=500)
        
        @app.get("/health")
        async def health_check():
            agent_statuses = {}
            for agent_name, agent_info in self.agents.items():
                try:
                    health_response = requests.get(f"{agent_info['url']}/health", timeout=2)
                    agent_statuses[agent_name] = "online" if health_response.status_code == 200 else "error"
                except:
                    agent_statuses[agent_name] = "offline"
            
            return {
                "status": "healthy",
                "agent": self.name,
                "role": "Multi-Agent Coordinator", 
                "registered_agents": len(self.agents),
                "agent_status": agent_statuses
            }
        
        @app.get("/system")
        async def system_overview():
            return {
                "system": "Multi-Agent RAG System",
                "coordinator": self.name,
                "agents": self.agents,
                "overview": self.get_system_overview()
            }
        
        @app.get("/")
        async def root():
            return {
                "agent": self.name,
                "role": "Multi-Agent Coordinator",
                "description": "Routes queries to specialized agents based on content analysis",
                "capabilities": [
                    "Query analysis and routing",
                    "Agent delegation",
                    "System coordination",
                    "Fallback handling"
                ],
                "registered_agents": list(self.agents.keys()),
                "endpoints": {
                    "POST /task": "Process and route queries",
                    "GET /health": "Health check with agent status",
                    "GET /system": "Complete system overview",
                    "GET /": "Coordinator information"
                }
            }
        
        print(f"🎯 Starting {self.name} (Multi-Agent Coordinator) on http://{host}:{port}")
        print("🏛️ System Architecture:")
        print("  🎯 MainAgent - Query routing and coordination")
        print(f"  😊 GreetingAgent - Social interaction (port {os.getenv('GREETING_AGENT_PORT', '8003')})")
        print(f"  🏢 HRAgent - Employee data and analytics (port {os.getenv('HR_AGENT_PORT', '8002')})")
        print()
        print("🔗 Agent Communication:")
        print("  User → MainAgent → Specialized Agent → MCP Server → Database")
        print()
        
        uvicorn.run(app, host=host, port=port)

# Create the enhanced main agent
main_agent = MainAgent()

if __name__ == "__main__":
    print("🎯 Enhanced MainAgent - Multi-Agent Coordinator")
    print("=" * 50)
    print("🏛️ System Capabilities:")
    print("  🔍 Intelligent query analysis")
    print("  🎯 Smart agent delegation")
    print("  🤝 Agent-to-agent communication")
    print("  🔄 Automatic fallback handling")
    print("  📊 System health monitoring")
    print()
    print("🤖 Registered Agents:")
    for agent_name, agent_info in main_agent.agents.items():
        print(f"  {agent_name.title()}Agent: {agent_info['specialization']}")
    print()
    
    # Start the main coordinating agent
    host = os.getenv("MAIN_AGENT_HOST", "localhost") 
    port = int(os.getenv("MAIN_AGENT_PORT", "8001"))
    
    main_agent.serve(host=host, port=port)
