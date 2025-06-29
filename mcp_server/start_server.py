"""
Simple MCP Server Startup Script
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import and run the server
from mcp_server.server import mcp

if __name__ == "__main__":
    import asyncio
    
    print("🚀 Starting Employee Database MCP Server...")
    print("📡 Access at: http://localhost:8000/mcp")
    print("💡 Press Ctrl+C to stop")
    print()
    
    try:
        # Use asyncio to run the HTTP server
        asyncio.run(mcp.run_http_async(
            transport="http", 
            host="localhost", 
            port=8000,
            path="/mcp"
        ))
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
