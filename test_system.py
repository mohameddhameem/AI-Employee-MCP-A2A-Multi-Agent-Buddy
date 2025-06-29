#!/usr/bin/env python3
"""
Test the complete MainAgent + MCP system
"""

import requests
import json

# Test configurations
MAIN_AGENT_URL = "http://localhost:8001"
MCP_SERVER_URL = "http://localhost:8000"

def test_system():
    print("🧪 Testing Complete Multi-Agent RAG System")
    print("=" * 50)
    
    # Test 1: Health checks
    print("1. 🏥 Health Checks:")
    try:
        mcp_health = requests.get(f"{MCP_SERVER_URL}/health").json()
        print(f"   ✅ MCP Server: {mcp_health['status']} - {mcp_health['employee_count']} employees")
        
        agent_health = requests.get(f"{MAIN_AGENT_URL}/health").json()
        print(f"   ✅ MainAgent: {agent_health['status']}")
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
        return
    
    print()
    
    # Test 2: Sample queries
    test_queries = [
        "List all employees in Engineering",
        "Show me the department summary", 
        "Find employees with John in their name",
        "How many employees do we have total?"
    ]
    
    print("2. 🤖 Agent Query Tests:")
    for i, query in enumerate(test_queries, 1):
        try:
            response = requests.post(
                f"{MAIN_AGENT_URL}/task",
                json={"input": query},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Test {i}: {query}")
                print(f"      Result: {result.get('result', 'No result')[:100]}...")
            else:
                print(f"   ❌ Test {i}: {query} - Status: {response.status_code}")
                print(f"      Error: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Test {i}: {query} - Exception: {e}")
        
        print()
    
    print("🎉 Phase 4 Testing Complete!")
    print("=" * 50)

if __name__ == "__main__":
    test_system()
