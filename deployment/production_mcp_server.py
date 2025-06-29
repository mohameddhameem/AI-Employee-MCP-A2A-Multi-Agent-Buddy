#!/usr/bin/env python3
"""
Phase 8: Local Deployment - Production Server with Uvicorn
Enhanced HTTP server with production features for MCP server
"""

import os
import sys
import uvicorn
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from mcp_server.http_server import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Run production MCP server with Uvicorn"""
    
    # Get configuration from environment
    host = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_SERVER_PORT", "8000"))
    workers = int(os.getenv("MCP_SERVER_WORKERS", "1"))
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    logger.info(f"Starting MCP Server on {host}:{port}")
    logger.info(f"Workers: {workers}, Log Level: {log_level}")
    
    # Run with Uvicorn
    uvicorn.run(
        "mcp_server.http_server:app",
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
    main()
