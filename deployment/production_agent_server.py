#!/usr/bin/env python3
"""
Phase 8: Local Deployment - Production Agent Server
Enhanced HTTP server with production features for agents
"""

import os
import sys
import uvicorn
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

def run_agent_server(agent_module: str, agent_name: str, default_port: int):
    """Run production agent server with Uvicorn"""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    # Get configuration from environment
    host = os.getenv(f"{agent_name.upper()}_HOST", "0.0.0.0")
    port = int(os.getenv(f"{agent_name.upper()}_PORT", str(default_port)))
    workers = int(os.getenv(f"{agent_name.upper()}_WORKERS", "1"))
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    logger.info(f"Starting {agent_name} Agent on {host}:{port}")
    logger.info(f"Workers: {workers}, Log Level: {log_level}")
    
    # Run with Uvicorn
    uvicorn.run(
        f"{agent_module}:app",
        host=host,
        port=port,
        workers=workers,
        log_level=log_level,
        reload=False,  # Disable reload in production
        access_log=True,
        use_colors=True,
        server_header=False,  # Security: hide server header
        date_header=False,    # Security: hide date header
    )

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python production_agent_server.py <agent_type>")
        print("Available agents: main, hr, greeting")
        sys.exit(1)
    
    agent_type = sys.argv[1].lower()
    
    agent_configs = {
        "main": ("agents.main_agent_a2a", "MAIN_AGENT", 8001),
        "hr": ("agents.hr_agent_a2a", "HR_AGENT", 8002),
        "greeting": ("agents.greeting_agent_a2a", "GREETING_AGENT", 8003),
    }
    
    if agent_type not in agent_configs:
        print(f"Unknown agent type: {agent_type}")
        print("Available agents: main, hr, greeting")
        sys.exit(1)
    
    module, name, port = agent_configs[agent_type]
    run_agent_server(module, name, port)
