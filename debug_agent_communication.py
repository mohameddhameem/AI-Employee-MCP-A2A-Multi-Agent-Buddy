#!/usr/bin/env python3
"""
Debug Agent Communication for Phase 7
Simple direct test to verify agent connectivity
"""

import sys
import asyncio
import aiohttp
from pathlib import Path

# Add project root to Python path  
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from a2a.protocol import A2AProtocol, MessageType

async def test_direct_agent_communication():
    """Test direct communication with each agent"""
    print("🔍 Testing Direct Agent Communication")
    print("=" * 50)
    
    # Test A2A protocol
    test_a2a = A2AProtocol(
        agent_id='debug_test_agent',
        agent_name='DebugTestAgent',
        endpoint='http://localhost:9999',
        secret_key='rag_a2a_mcp_secret'
    )
    
    agents_to_test = {
        "hr_agent_specialist": "http://localhost:8002",
        "greeting_agent_social": "http://localhost:8003", 
        "main_agent_coordinator": "http://localhost:8001"
    }
    
    for agent_id, endpoint in agents_to_test.items():
        print(f"\n🧪 Testing {agent_id} at {endpoint}")
        
        try:
            # Test 1: Health check
            print("  1️⃣ Health check...")
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{endpoint}/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        health_data = await response.json()
                        print(f"     ✅ Health: {health_data.get('status', 'unknown')}")
                    else:
                        print(f"     ❌ Health check failed: {response.status}")
                        continue
            
            # Test 2: Basic endpoint info
            print("  2️⃣ Basic info...")
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{endpoint}/", timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        info_data = await response.json()
                        print(f"     ✅ Agent: {info_data.get('agent', 'unknown')}")
                    else:
                        print(f"     ❌ Info request failed: {response.status}")
            
            # Test 3: A2A delegation  
            print("  3️⃣ A2A delegation...")
            delegation_message = test_a2a.create_message(
                MessageType.DELEGATION_REQUEST,
                agent_id,
                {
                    "task": "Simple test task",
                    "input_data": {"test": True},
                    "task_id": f"debug_test_{agent_id}",
                    "metadata": {"debug": True}
                }
            )
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{endpoint}/a2a",
                    json=delegation_message.to_dict(),
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        delegation_data = await response.json()
                        if delegation_data.get("message_type") == "delegation_response":
                            print(f"     ✅ A2A delegation: SUCCESS")
                            print(f"     📝 Response status: {delegation_data.get('payload', {}).get('status', 'unknown')}")
                        else:
                            print(f"     ❌ A2A delegation: Wrong message type")
                            print(f"     📝 Response: {delegation_data}")
                    else:
                        print(f"     ❌ A2A delegation failed: {response.status}")
                        response_text = await response.text()
                        print(f"     📝 Error: {response_text}")
            
        except Exception as e:
            print(f"     ❌ Agent test failed: {str(e)}")

async def main():
    """Run direct communication tests"""
    print("🔍 Phase 7 Debug: Direct Agent Communication Test")
    print("=" * 60)
    
    await test_direct_agent_communication()
    
    print("\n" + "=" * 60)
    print("🎯 Debug test completed!")

if __name__ == "__main__":
    asyncio.run(main())
