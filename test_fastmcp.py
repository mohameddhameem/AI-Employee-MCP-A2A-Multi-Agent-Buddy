#!/usr/bin/env python3
"""
Test the FastMCP server using proper MCP protocol
"""

import requests
import json

def test_mcp_tool_call(tool_name, arguments=None):
    """Test calling an MCP tool via HTTP"""
    url = "http://localhost:8000/mcp"
    
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments or {}
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }
    
    try:
        print(f"🔧 Testing tool: {tool_name}")
        print(f"📤 Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        print(f"📥 Status: {response.status_code}")
        print(f"📥 Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            result = data.get("result")
            if result:
                print(f"✅ Success! Got {len(result) if isinstance(result, list) else 'data'}")
                if isinstance(result, list) and len(result) > 0:
                    print(f"📋 Sample: {result[0] if result else 'No data'}")
            else:
                print(f"⚠️  No result in response: {data}")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print("-" * 50)

def test_mcp_resource():
    """Test accessing an MCP resource"""
    url = "http://localhost:8000/mcp"
    
    payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "resources/read", 
        "params": {
            "uri": "employees://all"
        }
    }
    
    try:
        print("🔧 Testing resource: employees://all")
        response = requests.post(url, json=payload, headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        })
        print(f"📥 Status: {response.status_code}")
        print(f"📥 Response: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print("-" * 50)

def main():
    print("🧪 Testing FastMCP Server with Proper MCP Protocol")
    print("=" * 60)
    
    # Test MCP tools
    test_mcp_tool_call("get_all_employees")
    test_mcp_tool_call("get_employees_by_department", {"department": "Engineering"})
    test_mcp_tool_call("get_department_summary")
    test_mcp_tool_call("health_check")
    
    # Test MCP resources
    test_mcp_resource()
    
    print("🎯 FastMCP Testing Complete!")

if __name__ == "__main__":
    main()
