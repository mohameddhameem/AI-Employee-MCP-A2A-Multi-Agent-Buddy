# CLI driver for MainAgent using ADK and MCP
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

# ADK agent endpoint
host = os.getenv("ADK_AGENT_HOST", "localhost")
port = os.getenv("ADK_AGENT_PORT", "8001")
agent_url = f"http://{host}:{port}"  # default ADK HTTP API root

import logging
from common.logging_config import configure_logging

configure_logging()
logger = logging.getLogger(__name__)

logger.info("Starting CLI for MainAgent")
logger.info(f"Sending queries to {agent_url}")
logger.info("Type 'exit' or 'quit' to stop.")

while True:
    query = input(">>> ")
    if query.lower() in ("exit", "quit"):
        print("Goodbye!")
        break

    # Send query to ADK agent
    try:
        response = requests.post(
            f"{agent_url}/task", json={"input": query}, headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        data = response.json()
        result = data.get("result") or data.get("output") or data
        logger.info(f"Response:\n{result}\n")
    except Exception as e:
        logger.error(f"Error communicating with agent: {e}")
