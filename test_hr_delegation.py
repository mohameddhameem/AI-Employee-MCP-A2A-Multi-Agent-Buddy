#!/usr/bin/env python3
"""
Test HR Agent A2A Delegation
Quick test to verify HR agent delegation fix
"""

import sys
import json
import time
import requests
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from a2a.protocol import A2AProtocol, MessageType

def test_hr_delegation():
    """Test HR agent delegation specifically"""
    
    print("🧪 Testing HR Agent A2A Delegation Fix")
    print("=" * 50)
    
    # Wait for agents to fully start
    print("⏳ Waiting 3 seconds for agents to stabilize...")
    time.sleep(3)
    
    # Create test A2A protocol
    test_a2a = A2AProtocol(
        agent_id='test_agent',
        agent_name='TestAgent', 
        endpoint='http://localhost:9999',
        secret_key='rag_a2a_mcp_secret'
    )
    
    # Test HR agent delegation
    print("\n🏢 Testing HR Agent Delegation...")
    
    try:
        # Create delegation message
        delegation_message = test_a2a.create_message(
            MessageType.DELEGATION_REQUEST,
            'hr_agent',
            {
                'task': 'List all employees',
                'context': {'test_mode': True},
                'priority': 'normal'
            }
        )
        
        print(f"📤 Sending delegation request...")
        print(f"   Message ID: {delegation_message.message_id}")
        print(f"   Message Type: {delegation_message.message_type.value}")
        print(f"   Task: {delegation_message.payload['task']}")
        
        # Send to HR agent
        response = requests.post(
            'http://localhost:8002/a2a',
            json=delegation_message.to_dict(),
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"\n📥 Response received:")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check response format
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
                    print("   ✅ HR delegation working correctly!")
                    
                    # Check if result contains employee data
                    if any(keyword in result.lower() for keyword in ['employee', 'directory', 'name']):
                        print("   ✅ Response contains expected employee data!")
                        return True
                    else:
                        print("   ❌ Response missing expected employee data")
                        print(f"   Result preview: {result[:100]}...")
                        return False
                else:
                    print(f"   ❌ Unexpected status or empty result: {status}")
                    return False
            else:
                print(f"   ❌ Wrong message type. Expected: {MessageType.DELEGATION_RESPONSE.value}")
                print(f"   Full response: {json.dumps(data, indent=2)}")
                return False
        else:
            print(f"   ❌ HTTP error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Test failed with exception: {str(e)}")
        return False

def main():
    """Run the focused HR delegation test"""
    
    print("🚀 Starting HR Agent Delegation Test")
    print(f"⏰ Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test HR delegation
    success = test_hr_delegation()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    
    if success:
        print("✅ HR Agent Delegation: WORKING")
        print("🎉 Phase 6 A2A Protocol: FULLY FUNCTIONAL")
        print("🚀 Ready to proceed to Phase 7!")
    else:
        print("❌ HR Agent Delegation: STILL FAILING")
        print("🔧 Phase 6 A2A Protocol: NEEDS MORE FIXING")
        print("⚠️  Must resolve delegation issue before Phase 7")
    
    return success

if __name__ == "__main__":
    main()
