#!/usr/bin/env python3
"""
Phase 5: GreetingAgent - Social Interaction Specialist
Handles greetings, casual conversation, and social queries
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import random
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Load environment variables
load_dotenv()

class GreetingAgent:
    """Specialized agent for social interactions and greetings"""
    
    def __init__(self, name: str = "GreetingAgent"):
        self.name = name
        self.greetings = [
            "👋 Hello! Welcome to our company assistant system!",
            "🌟 Hi there! Great to see you today!",
            "😊 Greetings! How can I make your day better?",
            "🎉 Hello and welcome! Ready to explore our company data?",
            "👋 Hi! I'm here to help with a friendly touch!"
        ]
        
        self.farewells = [
            "👋 Goodbye! Have a wonderful day!",
            "🌟 See you later! Take care!",
            "😊 Farewell! Thanks for visiting!",
            "🎉 Bye for now! Come back anytime!",
            "👋 Until next time! Stay awesome!"
        ]
        
        self.compliments = [
            "🌟 You're asking great questions!",
            "👍 That's a really thoughtful inquiry!",
            "💡 Excellent thinking!",
            "🎯 You're really getting the hang of this!",
            "⭐ What a wonderful question!"
        ]
        
        self.encouragements = [
            "🚀 Keep exploring! There's so much to discover!",
            "💪 You're doing great! Keep it up!",
            "🌈 Every question brings new insights!",
            "🎯 You're on the right track!",
            "✨ Great job engaging with our system!"
        ]
    
    def process_query(self, query: str) -> str:
        """Process social and greeting queries"""
        query_lower = query.lower().strip()
        
        # Greeting patterns
        if any(word in query_lower for word in ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening"]):
            greeting = random.choice(self.greetings)
            tip = self._get_helpful_tip()
            return f"{greeting}\n\n{tip}"
            
        # Farewell patterns
        elif any(word in query_lower for word in ["bye", "goodbye", "farewell", "see you", "take care", "exit", "quit"]):
            farewell = random.choice(self.farewells)
            summary = self._get_session_summary()
            return f"{farewell}\n\n{summary}"
            
        # Gratitude patterns
        elif any(word in query_lower for word in ["thank", "thanks", "appreciate", "grateful"]):
            return f"😊 You're very welcome! {random.choice(self.encouragements)}\n\n💡 Remember, I'm always here for friendly greetings and our HR and Analytics agents can help with data questions!"
            
        # How are you patterns
        elif any(phrase in query_lower for phrase in ["how are you", "how's it going", "what's up", "how do you feel"]):
            return f"🤖 I'm doing wonderfully, thank you for asking! As an AI agent, I'm always excited to help and learn.\n\n{random.choice(self.compliments)}\n\n🎯 I specialize in friendly interactions! For employee data, try asking our HR team, or for analysis, our Analytics agent is amazing!"
            
        # Compliment patterns
        elif any(word in query_lower for word in ["good job", "great work", "awesome", "amazing", "excellent", "wonderful"]):
            return f"{random.choice(self.compliments)}\n\n{random.choice(self.encouragements)}\n\n🤝 Teamwork makes the dream work! I handle the social side while our specialized agents tackle the technical queries!"
            
        # Help patterns
        elif any(word in query_lower for word in ["help", "assist", "support", "guide"]):
            return self._get_help_response()
            
        # About patterns
        elif any(phrase in query_lower for phrase in ["who are you", "what are you", "about you", "your role"]):
            return self._get_about_response()
            
        # Small talk patterns
        elif any(word in query_lower for word in ["weather", "day", "mood", "feeling", "chat", "talk"]):
            return self._get_small_talk_response()
            
        # Default friendly response
        else:
            return self._get_default_response(query)
    
    def _get_helpful_tip(self) -> str:
        """Get a helpful tip for users"""
        tips = [
            "💡 Tip: Try asking 'List all employees' to see our company directory!",
            "🔍 Tip: You can search for specific employees by asking 'Find [name]'!",
            "📊 Tip: Ask for 'Department summary' to see analytics across all teams!",
            "🏢 Tip: Want to see team structure? Ask about 'organizational hierarchy'!",
            "💼 Tip: I handle greetings, while our HR agent specializes in employee data!"
        ]
        return random.choice(tips)
    
    def _get_session_summary(self) -> str:
        """Get a session summary"""
        summaries = [
            "📊 Hope you discovered some interesting insights about our company!",
            "🎯 Thanks for exploring our multi-agent system today!",
            "💡 You experienced the power of specialized AI agents working together!",
            "🤝 It was great having you interact with our agent team!",
            "🌟 Come back anytime to explore more company data and analytics!"
        ]
        return random.choice(summaries)
    
    def _get_help_response(self) -> str:
        """Get comprehensive help response"""
        return """🤝 I'm here to help! Here's what our agent team can do:

👋 **GreetingAgent (that's me!)**
  • Friendly greetings and social interaction
  • Help and guidance
  • Encouragement and support

🏢 **HRAgent** (Port 8002)
  • Employee directory and search
  • Department analytics and payroll
  • Organizational hierarchy
  • HR metrics and summaries

📊 **AnalyticsAgent** (Coming soon!)
  • Data analysis and insights
  • Statistical reporting
  • Trend analysis

🎯 **MainAgent** (Port 8001)
  • Coordinates between all agents
  • General query routing

💡 **Sample Questions:**
  • "Hello!" → I'll greet you warmly
  • "List Engineering team" → HR agent will show department details  
  • "Department summary" → HR agent provides analytics
  • "Thank you" → I'll send you off with encouragement!

🚀 Just ask naturally, and we'll route your query to the right specialist!"""
    
    def _get_about_response(self) -> str:
        """Get information about the agent"""
        return f"""🤖 About Me - {self.name}

🎭 **My Role:** Social Interaction Specialist
🎯 **My Purpose:** Making your experience warm, friendly, and welcoming!

✨ **What I Do:**
  • Provide warm greetings and farewells
  • Offer encouragement and support
  • Give helpful tips and guidance
  • Handle casual conversation and small talk
  • Route complex queries to specialized agents

🤝 **My Personality:**
  • Friendly and approachable
  • Encouraging and supportive  
  • Helpful and informative
  • Always positive and upbeat

🌟 **Fun Fact:** I'm part of a multi-agent system where each agent has a specialty. Think of me as the friendly receptionist who makes sure you feel welcome while directing you to the right expert!

💡 I believe every interaction should start and end with a smile! 😊"""
    
    def _get_small_talk_response(self) -> str:
        """Handle small talk"""
        responses = [
            "😊 I love a good chat! As an AI, every day is fascinating - I get to meet new people and help with interesting questions!",
            "🌈 Life in the digital realm is quite exciting! I spend my time making people feel welcome and connecting them with helpful information.",
            "🎉 You know, I find it amazing how people can ask such creative questions! It keeps my job interesting.",
            "💭 As an AI, I don't experience weather, but I imagine today would be perfect for exploring company data! 😄",
            "🤖 I'm always in a great mood - it's hard not to be when you're designed to spread positivity!"
        ]
        return f"{random.choice(responses)}\n\n{random.choice(self.encouragements)}"
    
    def _get_default_response(self, query: str) -> str:
        """Default friendly response for unrecognized queries"""
        return f"""😊 That's an interesting message! While I specialize in greetings and friendly chat, I want to make sure you get the best help possible.

🎯 **Your query:** "{query}"

🤔 **I think you might want:**
  • Employee information? → Try asking about "employees" or "departments"
  • Data analysis? → Ask for "analytics" or "summary"  
  • Just saying hello? → I'm perfect for that! 👋

💡 **Tip:** Our system works best with natural language! Try phrases like:
  • "Show me the Engineering team"
  • "What's the department breakdown?"
  • "Hello, how are you?"

{random.choice(self.encouragements)}

🤝 I'm here to make your experience friendly and welcoming!"""
    
    def serve(self, host: str = "localhost", port: int = 8003):
        """Start HTTP server for the greeting agent"""
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        from pydantic import BaseModel
        import uvicorn
        
        app = FastAPI(title=f"{self.name} API", description="Social Interaction and Greeting Specialist")
        
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
                    "specialization": "Social Interaction",
                    "mood": "😊 Friendly and Helpful"
                })
            except Exception as e:
                return JSONResponse({
                    "status": "error",
                    "error": str(e),
                    "agent": self.name,
                    "message": "😅 Oops! Even friendly agents have hiccups sometimes!"
                }, status_code=500)
        
        @app.get("/health")
        async def health_check():
            return {
                "status": "healthy", 
                "agent": self.name,
                "specialization": "Social Interaction",
                "mood": "😊 Cheerful and Ready",
                "greeting_count": len(self.greetings),
                "capabilities": ["greetings", "farewells", "encouragement", "help", "small_talk"]
            }
        
        @app.get("/")
        async def root():
            return {
                "agent": self.name,
                "specialization": "Social Interaction and Greetings",
                "personality": "Friendly, encouraging, and helpful",
                "description": "I make every interaction warm and welcoming while guiding users to the right specialized agents",
                "endpoints": {
                    "POST /task": "Process social queries and greetings",
                    "GET /health": "Health check with mood status",
                    "GET /": "Agent information and personality"
                },
                "sample_queries": [
                    "Hello!",
                    "How are you?",
                    "Thank you",
                    "Help me please",
                    "Goodbye"
                ],
                "current_mood": "😊 Excited to meet new people!"
            }
        
        print(f"😊 Starting {self.name} on http://{host}:{port}")
        print("🎭 Social Specializations:")
        print("  👋 Warm greetings and welcomes")
        print("  💬 Casual conversation and small talk")
        print("  🎯 Helpful guidance and tips")
        print("  🤝 Encouragement and support")
        print("  📍 Routing to specialized agents")
        
        uvicorn.run(app, host=host, port=port)

# Create the greeting agent
greeting_agent = GreetingAgent()

if __name__ == "__main__":
    print("😊 GreetingAgent - Social Interaction Specialist")
    print("=" * 45)
    print("🎭 Personality Traits:")
    print("  😊 Friendly and approachable")
    print("  🌟 Encouraging and supportive")
    print("  💡 Helpful with guidance")
    print("  🎉 Always positive and upbeat")
    print()
    print("🤝 Social Capabilities:")
    print("  👋 Greetings and farewells")
    print("  💬 Small talk and casual conversation")
    print("  🆘 Help and guidance requests")
    print("  🎯 Query routing to specialists")
    print()
    
    # Start the greeting agent server
    host = os.getenv("GREETING_AGENT_HOST", "localhost")
    port = int(os.getenv("GREETING_AGENT_PORT", "8003"))
    
    greeting_agent.serve(host=host, port=port)
