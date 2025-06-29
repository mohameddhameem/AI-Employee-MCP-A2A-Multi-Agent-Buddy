#!/usr/bin/env python3
"""
Debug coordination delegation
"""

import asyncio
import aiohttp
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from a2a.protocol import A2AProtocol, MessageType

async def test_direct_delegation():
    """Test direct A2A delegation"""
    print("🔍 Testing Direct A2A Delegation")
    print("-" * 40)
    
    # Create test A2A protocol
    test_a2a = A2AProtocol(
        agent_id='test_orchestrator',
        agent_name='TestOrchestrator', 
        endpoint='http://localhost:9999',
        secret_key='rag_a2a_mcp_secret'
    )
    
    # Test HR agent delegation
    print("🏢 Testing HR Agent Direct Delegation...")
    
    try:
        # Create delegation message
        delegation_message = test_a2a.create_message(
            MessageType.DELEGATION_REQUEST,
            'hr_agent_specialist',
            {
                'task': 'List all employees',
                'input_data': {'query': 'List all employees'},
                'task_id': 'test_task_001',
                'metadata': {'test': True}
            }
        )
        
        print(f"📤 Sending delegation to HR agent...")
        print(f"   Target: http://localhost:8002/a2a")
        print(f"   Message ID: {delegation_message.message_id}")
        print(f"   Task: {delegation_message.payload['task']}")
        
        # Send to HR agent
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'http://localhost:8002/a2a',
                json=delegation_message.to_dict(),
                headers={'Content-Type': 'application/json'},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                
                print(f"\n📥 Response received:")
                print(f"   Status Code: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    
                    message_type = data.get('message_type')
                    print(f"   Message Type: {message_type}")
                    
                    if message_type == MessageType.DELEGATION_RESPONSE.value:
                        print("   ✅ Correct message type!")
                        
                        payload = data.get('payload', {})
                        status = payload.get('status')
                        result = payload.get('result', '')
                        
                        print(f"   Status: {status}")
                        print(f"   Has result: {'Yes' if result else 'No'}")
                        
                        if status == 'success' and result:
                            print("   ✅ HR delegation working!")
                            print(f"   Result preview: {str(result)[:200]}...")
                            return True
                        else:
                            print(f"   ❌ Unexpected status or empty result")
                            return False
                    else:
                        print(f"   ❌ Wrong message type")
                        print(f"   Full response: {data}")
                        return False
                else:
                    print(f"   ❌ HTTP error: {response.status}")
                    text = await response.text()
                    print(f"   Response: {text}")
                    return False
                    
    except Exception as e:
        print(f"   ❌ Test failed with exception: {str(e)}")
        return False

async def main():
    """Run direct delegation test"""
    print("🚀 Direct A2A Delegation Test")
    print("=" * 40)
    
    success = await test_direct_delegation()
    
    print(f"\n{'='*40}")
    print("TEST RESULTS:")
    
    if success:
        print("✅ Direct delegation: WORKING")
        print("🎉 A2A protocol communication: FUNCTIONAL")
    else:
        print("❌ Direct delegation: FAILING") 
        print("🔧 Need to investigate A2A communication")

if __name__ == "__main__":
    asyncio.run(main())
