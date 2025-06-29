#!/usr/bin/env python3
"""
Phase 7: Simple Coordination Test
Quick test of the multi-agent coordination system
"""

import asyncio
import sys
import time
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from coordination.orchestrator import (
    MultiAgentOrchestrator, TaskNode, CoordinationPattern, TaskStatus
)

async def test_simple_sequential_workflow():
    """Test a simple sequential workflow"""
    print("🧪 Testing Simple Sequential Workflow")
    print("-" * 40)
    
    # Create orchestrator
    orchestrator = MultiAgentOrchestrator()
    
    # Wait for agents to be ready
    print("⏳ Waiting 5 seconds for agents to start...")
    await asyncio.sleep(5)
    
    # Define a simple sequential workflow
    tasks = [
        TaskNode(
            task_id="get_employees",
            description="Get list of all employees",
            agent_id="hr_agent_specialist",
            input_data={"query": "List all employees"},
            metadata={"step": 1}
        ),
        TaskNode(
            task_id="greet_team",
            description="Generate a team greeting message",
            agent_id="greeting_agent_social", 
            input_data={"occasion": "team_meeting", "message": "Welcome everyone!"},
            metadata={"step": 2}
        )
    ]
    
    print(f"📋 Executing workflow with {len(tasks)} tasks")
    print(f"🎯 Tasks: {[task.task_id for task in tasks]}")
    print(f"🤖 Agents: {[task.agent_id for task in tasks]}")
    
    try:
        # Execute the workflow
        result = await orchestrator.execute_workflow(
            workflow_id="simple_test_001",
            tasks=tasks,
            pattern=CoordinationPattern.SEQUENTIAL,
            context={"test_mode": True}
        )
        
        print(f"\n✅ Workflow completed!")
        print(f"📊 Status: {result.status.value}")
        print(f"⏱️ Execution time: {result.execution_time:.2f}s")
        print(f"📝 Summary: {result.summary}")
        
        if result.metrics:
            print(f"📈 Success rate: {result.metrics['success_rate']:.1%}")
            print(f"🔢 Task count: {result.metrics['task_count']}")
            print(f"👥 Agent count: {result.metrics['agent_count']}")
        
        # Show task results
        print(f"\n📋 Individual Task Results:")
        for task_id, task in result.task_results.items():
            status_emoji = "✅" if task.status == TaskStatus.COMPLETED else "❌"
            print(f"  {status_emoji} {task_id}: {task.status.value}")
            if task.result:
                result_preview = str(task.result)[:100]
                print(f"    💬 Result preview: {result_preview}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Workflow failed: {str(e)}")
        return False

async def test_simple_parallel_workflow():
    """Test a simple parallel workflow"""
    print("\n🧪 Testing Simple Parallel Workflow")
    print("-" * 40)
    
    orchestrator = MultiAgentOrchestrator()
    
    # Define parallel tasks
    tasks = [
        TaskNode(
            task_id="hr_analysis",
            description="Get HR analytics summary",
            agent_id="hr_agent_specialist",
            input_data={"query": "HR analytics summary"},
            metadata={"department": "hr"}
        ),
        TaskNode(
            task_id="team_greeting",
            description="Generate motivational team message",
            agent_id="greeting_agent_social",
            input_data={"occasion": "daily_standup", "tone": "motivational"},
            metadata={"department": "social"}
        )
    ]
    
    print(f"📋 Executing parallel workflow with {len(tasks)} tasks")
    
    try:
        result = await orchestrator.execute_workflow(
            workflow_id="parallel_test_001",
            tasks=tasks,
            pattern=CoordinationPattern.PARALLEL,
            context={"test_mode": True, "parallel_execution": True}
        )
        
        print(f"✅ Parallel workflow completed!")
        print(f"📊 Status: {result.status.value}")
        print(f"⏱️ Execution time: {result.execution_time:.2f}s")
        print(f"📝 Summary: {result.summary}")
        
        return True
        
    except Exception as e:
        print(f"❌ Parallel workflow failed: {str(e)}")
        return False

async def main():
    """Run coordination tests"""
    print("🎭 Phase 7: Multi-Agent Coordination Test")
    print("=" * 50)
    
    # Test sequential workflow
    sequential_success = await test_simple_sequential_workflow()
    
    # Test parallel workflow 
    parallel_success = await test_simple_parallel_workflow()
    
    # Summary
    print(f"\n{'='*50}")
    print("COORDINATION TEST RESULTS")
    print('='*50)
    
    print(f"🔄 Sequential workflow: {'✅ PASS' if sequential_success else '❌ FAIL'}")
    print(f"⚡ Parallel workflow: {'✅ PASS' if parallel_success else '❌ FAIL'}")
    
    if sequential_success and parallel_success:
        print(f"\n🎉 Phase 7 Multi-Agent Coordination: FUNCTIONAL!")
        print(f"🚀 Ready for advanced workflow patterns!")
    else:
        print(f"\n⚠️ Some coordination patterns need debugging")
    
    return sequential_success and parallel_success

if __name__ == "__main__":
    asyncio.run(main())
