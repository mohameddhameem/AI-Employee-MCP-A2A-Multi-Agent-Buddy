#!/usr/bin/env python3
"""
Phase 7: Multi-Agent Coordination Test
Test the orchestrator with various coordination patterns
"""

import sys
import asyncio
import time
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from coordination.orchestrator import (
    MultiAgentOrchestrator, 
    TaskNode, 
    CoordinationPattern,
    TaskStatus
)

async def test_sequential_coordination():
    """Test sequential coordination pattern"""
    print("\n🔄 Testing Sequential Coordination")
    print("=" * 50)
    
    orchestrator = MultiAgentOrchestrator()
    
    # Create a sequential workflow: Greeting → HR Info → Summary
    tasks = [
        TaskNode(
            task_id="greeting_task",
            description="Provide a friendly greeting",
            agent_id="greeting_agent_social",
            input_data={"user_name": "Alice"}
        ),
        TaskNode(
            task_id="hr_info_task", 
            description="Get employee information",
            agent_id="hr_agent_specialist",
            input_data={"query": "List all employees"}
        ),
        TaskNode(
            task_id="summary_task",
            description="Summarize the interaction",
            agent_id="main_agent_coordinator", 
            input_data={"task": "Create a summary of the previous interactions"}
        )
    ]
    
    # Execute sequential workflow
    result = await orchestrator.execute_workflow(
        workflow_id="sequential_test_001",
        tasks=tasks,
        pattern=CoordinationPattern.SEQUENTIAL,
        context={"test_mode": True, "user": "Alice"}
    )
    
    print(f"✅ Sequential workflow result: {result.status.value}")
    print(f"📊 Execution time: {result.execution_time:.2f}s")
    print(f"📋 Summary: {result.summary}")
    
    return result

async def test_parallel_coordination():
    """Test parallel coordination pattern"""
    print("\n⚡ Testing Parallel Coordination")
    print("=" * 50)
    
    orchestrator = MultiAgentOrchestrator()
    
    # Create parallel tasks - all agents work simultaneously
    tasks = [
        TaskNode(
            task_id="greeting_parallel",
            description="Generate welcome message",
            agent_id="greeting_agent_social",
            input_data={"context": "Welcome new employee"}
        ),
        TaskNode(
            task_id="hr_parallel",
            description="Get department summary", 
            agent_id="hr_agent_specialist",
            input_data={"query": "Department summary"}
        ),
        TaskNode(
            task_id="main_parallel",
            description="Analyze current system status",
            agent_id="main_agent_coordinator",
            input_data={"task": "System status analysis"}
        )
    ]
    
    # Execute parallel workflow
    result = await orchestrator.execute_workflow(
        workflow_id="parallel_test_001",
        tasks=tasks,
        pattern=CoordinationPattern.PARALLEL,
        context={"test_mode": True, "simultaneous_execution": True}
    )
    
    print(f"✅ Parallel workflow result: {result.status.value}")
    print(f"📊 Execution time: {result.execution_time:.2f}s")
    print(f"📋 Summary: {result.summary}")
    
    return result

async def test_pipeline_coordination():
    """Test pipeline coordination pattern"""
    print("\n🔗 Testing Pipeline Coordination")
    print("=" * 50)
    
    orchestrator = MultiAgentOrchestrator()
    
    # Create pipeline: Greeting prepares → HR processes → Main synthesizes
    tasks = [
        TaskNode(
            task_id="pipeline_stage1",
            description="Prepare employee onboarding greeting",
            agent_id="greeting_agent_social",
            input_data={"new_employee": "Bob", "department": "Engineering"}
        ),
        TaskNode(
            task_id="pipeline_stage2", 
            description="Process employee data and department info",
            agent_id="hr_agent_specialist",
            input_data={"query": "Engineering department overview"}
        ),
        TaskNode(
            task_id="pipeline_stage3",
            description="Create comprehensive onboarding package",
            agent_id="main_agent_coordinator",
            input_data={"task": "Synthesize onboarding information"}
        )
    ]
    
    # Execute pipeline workflow
    result = await orchestrator.execute_workflow(
        workflow_id="pipeline_test_001",
        tasks=tasks,
        pattern=CoordinationPattern.PIPELINE,
        context={"test_mode": True, "new_employee_onboarding": True}
    )
    
    print(f"✅ Pipeline workflow result: {result.status.value}")
    print(f"📊 Execution time: {result.execution_time:.2f}s")
    print(f"📋 Summary: {result.summary}")
    
    return result

async def test_consensus_coordination():
    """Test consensus coordination pattern"""
    print("\n🤝 Testing Consensus Coordination")
    print("=" * 50)
    
    orchestrator = MultiAgentOrchestrator()
    
    # Create consensus tasks - same question to multiple agents
    tasks = [
        TaskNode(
            task_id="consensus_hr",
            description="What is the most important HR priority?",
            agent_id="hr_agent_specialist",
            input_data={"query": "What are the top HR priorities for our organization?"}
        ),
        TaskNode(
            task_id="consensus_main",
            description="What is the most important organizational priority?", 
            agent_id="main_agent_coordinator",
            input_data={"task": "Identify top organizational priorities"}
        ),
        TaskNode(
            task_id="consensus_greeting",
            description="What creates the best employee experience?",
            agent_id="greeting_agent_social", 
            input_data={"context": "Improving employee experience and satisfaction"}
        )
    ]
    
    # Execute consensus workflow
    result = await orchestrator.execute_workflow(
        workflow_id="consensus_test_001",
        tasks=tasks,
        pattern=CoordinationPattern.CONSENSUS,
        context={"test_mode": True, "decision_making": True}
    )
    
    print(f"✅ Consensus workflow result: {result.status.value}")
    print(f"📊 Execution time: {result.execution_time:.2f}s")
    print(f"📋 Summary: {result.summary}")
    
    return result

async def main():
    """Run all Phase 7 coordination tests"""
    print("🎭 Phase 7: Multi-Agent Coordination Tests")
    print("=" * 60)
    print(f"⏰ Test session started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = {}
    
    try:
        # Test 1: Sequential Coordination
        results["sequential"] = await test_sequential_coordination()
        
        # Brief pause between tests
        await asyncio.sleep(2)
        
        # Test 2: Parallel Coordination
        results["parallel"] = await test_parallel_coordination()
        
        # Brief pause between tests
        await asyncio.sleep(2)
        
        # Test 3: Pipeline Coordination
        results["pipeline"] = await test_pipeline_coordination()
        
        # Brief pause between tests
        await asyncio.sleep(2)
        
        # Test 4: Consensus Coordination
        results["consensus"] = await test_consensus_coordination()
        
        # Final Summary
        print("\n" + "=" * 60)
        print("📊 Phase 7 Coordination Test Results Summary")
        print("=" * 60)
        
        total_tests = len(results)
        successful_tests = sum(1 for r in results.values() if r.status == TaskStatus.COMPLETED)
        
        print(f"🎯 Tests Run: {total_tests}")
        print(f"✅ Successful: {successful_tests}")
        print(f"❌ Failed: {total_tests - successful_tests}")
        print(f"📈 Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        print()
        
        for pattern, result in results.items():
            status_icon = "✅" if result.status == TaskStatus.COMPLETED else "❌"
            print(f"{status_icon} {pattern.title()}: {result.execution_time:.2f}s - {result.metrics.get('success_rate', 0)*100:.1f}% task success")
        
        if successful_tests == total_tests:
            print("\n🎉 Phase 7 Multi-Agent Coordination: FULLY FUNCTIONAL!")
            print("🚀 Ready for advanced multi-agent workflows!")
        else:
            print(f"\n⚠️ {total_tests - successful_tests} coordination pattern(s) need attention")
            
    except Exception as e:
        print(f"\n❌ Test session failed: {str(e)}")
        return False
    
    return successful_tests == total_tests

if __name__ == "__main__":
    # Run the async test
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
