#!/usr/bin/env python3
"""
Simple Orchestrator Test - Debug specific issue
"""

import sys
import asyncio
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from coordination.orchestrator import (
    MultiAgentOrchestrator, 
    TaskNode, 
    CoordinationPattern
)

async def test_single_task():
    """Test a single task to isolate the issue"""
    print("🔍 Testing Single Task Execution")
    print("=" * 40)
    
    orchestrator = MultiAgentOrchestrator()
    
    # Test just the HR agent with a simple task
    task = TaskNode(
        task_id="debug_single_task",
        description="List all employees",  # Simple, known working task
        agent_id="hr_agent_specialist",
        input_data={"query": "List all employees"}
    )
    
    print(f"📤 Sending task to {task.agent_id}")
    print(f"📝 Task: {task.description}")
    
    try:
        result = await orchestrator._execute_single_task(task)
        print(f"✅ Task completed successfully!")
        print(f"📄 Result: {result}")
        return True
    except Exception as e:
        print(f"❌ Task failed: {str(e)}")
        print(f"🔍 Task status: {task.status}")
        print(f"🔍 Task error: {task.error}")
        return False

async def main():
    """Test single task execution"""
    print("🧪 Orchestrator Debug Test")
    print("=" * 30)
    
    success = await test_single_task()
    
    if success:
        print("\n🎉 Single task execution working!")
        print("🔄 Ready to test full workflows!")
    else:
        print("\n❌ Need to debug task execution...")

if __name__ == "__main__":
    asyncio.run(main())
