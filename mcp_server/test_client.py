"""
MCP Server Test Client
Tests the MCP server functionality
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any

class MCPTestClient:
    """Test client for MCP server"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.mcp_url = f"{base_url}/mcp"
    
    async def test_health_check(self) -> Dict[str, Any]:
        """Test the health check endpoint"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.base_url}/health") as response:
                    if response.status == 200:
                        return {"status": "success", "data": await response.json()}
                    else:
                        return {"status": "error", "code": response.status}
            except Exception as e:
                return {"status": "error", "error": str(e)}
    
    async def call_mcp_tool(self, tool_name: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call an MCP tool"""
        payload = {
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": params or {}
            }
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    self.mcp_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        return {"status": "success", "data": await response.json()}
                    else:
                        return {"status": "error", "code": response.status, "text": await response.text()}
            except Exception as e:
                return {"status": "error", "error": str(e)}
    
    async def get_mcp_resource(self, resource_uri: str) -> Dict[str, Any]:
        """Get an MCP resource"""
        payload = {
            "method": "resources/read",
            "params": {
                "uri": resource_uri
            }
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    self.mcp_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        return {"status": "success", "data": await response.json()}
                    else:
                        return {"status": "error", "code": response.status, "text": await response.text()}
            except Exception as e:
                return {"status": "error", "error": str(e)}

async def run_tests():
    """Run comprehensive MCP server tests"""
    print("🧪 MCP Server Test Suite")
    print("=" * 40)
    
    client = MCPTestClient()
    
    # Test 1: Health Check
    print("1️⃣ Testing Health Check...")
    health = await client.test_health_check()
    if health["status"] == "success":
        print("✅ Health check passed")
    else:
        print(f"❌ Health check failed: {health}")
        return
    
    # Test 2: Tool calls
    print("\n2️⃣ Testing MCP Tools...")
    
    tools_to_test = [
        ("health_check", {}),
        ("get_employee_summary", {}),
        ("get_department_summary", {}),
        ("get_employees_by_department", {"department": "Engineering"}),
        ("search_employees", {"search_term": "Alice"}),
        ("get_high_earners", {"threshold": 120000})
    ]
    
    for tool_name, params in tools_to_test:
        print(f"   Testing {tool_name}...")
        result = await client.call_mcp_tool(tool_name, params)
        if result["status"] == "success":
            print(f"   ✅ {tool_name} - OK")
        else:
            print(f"   ❌ {tool_name} - Failed: {result}")
    
    # Test 3: Resources
    print("\n3️⃣ Testing MCP Resources...")
    
    resources_to_test = [
        "employees://all",
        "employees://departments", 
        "employees://projects"
    ]
    
    for resource_uri in resources_to_test:
        print(f"   Testing {resource_uri}...")
        result = await client.get_mcp_resource(resource_uri)
        if result["status"] == "success":
            print(f"   ✅ {resource_uri} - OK")
        else:
            print(f"   ❌ {resource_uri} - Failed: {result}")
    
    print("\n🎉 Test suite completed!")

# Simple sync test for when server is not running
def test_server_offline():
    """Test what happens when server is offline"""
    print("🔌 Testing Server Connection...")
    print("=" * 30)
    
    import requests
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print("✅ Server is running!")
            return True
        else:
            print(f"⚠️ Server responded with status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Server is not running: {e}")
        print("💡 Start the server with: python mcp_server/server.py")
        return False

if __name__ == "__main__":
    # First test if server is running
    if test_server_offline():
        # Run async tests
        asyncio.run(run_tests())
    else:
        print("\n🚀 To test the MCP server:")
        print("1. Start server: python mcp_server/server.py")
        print("2. Run tests: python mcp_server/test_client.py")
