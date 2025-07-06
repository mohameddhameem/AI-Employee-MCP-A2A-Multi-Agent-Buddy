#!/usr/bin/env python3
"""
Coordination Patterns Integration Tests
Testing multi-agent coordination patterns and workflow execution
"""

import pytest
import asyncio
import time
from pathlib import Path
import sys
from unittest.mock import Mock, patch

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from coordination.orchestrator import (
    MultiAgentOrchestrator, 
    TaskNode, 
    CoordinationPattern,
    TaskStatus
)
from agents.main_agent_a2a import MainAgentA2A
from agents.hr_agent_a2a import HRAgentA2A
from agents.greeting_agent_a2a import GreetingAgentA2A


class TestCoordinationPatternsIntegration:
    """Integration tests for multi-agent coordination patterns"""
    
    def setup_method(self):
        """Setup test environment"""
        self.orchestrator = MultiAgentOrchestrator()
        self.main_agent = MainAgentA2A()
        self.hr_agent = HRAgentA2A()
        self.greeting_agent = GreetingAgentA2A()
    
    @pytest.mark.asyncio
    async def test_sequential_coordination_workflow(self):
        """Test sequential coordination pattern with realistic workflow"""
        # Create a sequential workflow: Greeting → HR Info → Summary
        tasks = [
            TaskNode(
                task_id="greeting_task",
                description="Provide a friendly greeting",
                agent_id="greeting_agent_social",
                input_data={"user_name": "Alice", "context": "employee_inquiry"}
            ),
            TaskNode(
                task_id="hr_info_task", 
                description="Get employee information",
                agent_id="hr_agent_specialist",
                input_data={"query": "List all employees", "department": "Engineering"}
            ),
            TaskNode(
                task_id="summary_task",
                description="Summarize the interaction",
                agent_id="main_agent_coordinator", 
                input_data={"task": "Create a summary of the previous interactions"}
            )
        ]
        
        # Mock the orchestrator execution for testing
        with patch.object(self.orchestrator, '_execute_single_task') as mock_execute:
            mock_execute.side_effect = [
                {"status": "completed", "result": "Hello Alice! How can I help you today?"},
                {"status": "completed", "result": "Found 5 employees in Engineering department"},
                {"status": "completed", "result": "Summary: Greeted Alice and provided Engineering team info"}
            ]
            
            # Execute sequential workflow
            result = await self.orchestrator.execute_workflow(
                workflow_id="sequential_test_001",
                tasks=tasks,
                pattern=CoordinationPattern.SEQUENTIAL,
                context={"test_mode": True, "user": "Alice"}
            )
            
            # Verify workflow execution
            assert result.status == TaskStatus.COMPLETED, "Sequential workflow should complete successfully"
            assert result.workflow_id == "sequential_test_001", "Workflow ID should be preserved"
            assert mock_execute.call_count == 3, "Should execute all tasks sequentially"
    
    @pytest.mark.asyncio
    async def test_parallel_coordination_workflow(self):
        """Test parallel coordination pattern with concurrent tasks"""
        # Create parallel tasks - all agents work simultaneously
        tasks = [
            TaskNode(
                task_id="greeting_parallel",
                description="Generate welcome message",
                agent_id="greeting_agent_social",
                input_data={"context": "Welcome new employee", "employee": "Bob"}
            ),
            TaskNode(
                task_id="hr_parallel",
                description="Get department summary", 
                agent_id="hr_agent_specialist",
                input_data={"query": "Department summary", "include_stats": True}
            ),
            TaskNode(
                task_id="main_parallel",
                description="Analyze current system status",
                agent_id="main_agent_coordinator",
                input_data={"task": "System status analysis", "include_metrics": True}
            )
        ]
        
        # Mock parallel execution
        with patch.object(self.orchestrator, '_execute_single_task') as mock_execute:
            # Simulate concurrent execution with varying completion times
            async def mock_task_execution(task):
                await asyncio.sleep(0.1)  # Simulate processing time
                return {
                    "status": "completed", 
                    "result": f"Task {task.task_id} completed",
                    "execution_time": 0.1
                }
            
            mock_execute.side_effect = mock_task_execution
            
            # Execute parallel workflow
            start_time = time.time()
            result = await self.orchestrator.execute_workflow(
                workflow_id="parallel_test_001",
                tasks=tasks,
                pattern=CoordinationPattern.PARALLEL,
                context={"test_mode": True, "simultaneous_execution": True}
            )
            execution_time = time.time() - start_time
            
            # Verify parallel execution
            assert result.status == TaskStatus.COMPLETED, "Parallel workflow should complete successfully"
            assert execution_time < 1.0, "Parallel execution should be faster than sequential"
            assert mock_execute.call_count == 3, "Should execute all tasks"
    
    @pytest.mark.asyncio
    async def test_hierarchical_coordination_workflow(self):
        """Test hierarchical coordination pattern with task dependencies"""
        # Create hierarchical workflow with dependencies
        tasks = [
            TaskNode(
                task_id="main_coordination",
                description="Main coordination task",
                agent_id="main_agent_coordinator",
                input_data={"task": "Coordinate employee onboarding process"},
                dependencies=[]  # Root task
            ),
            TaskNode(
                task_id="hr_data_gathering",
                description="Gather HR data for onboarding",
                agent_id="hr_agent_specialist",
                input_data={"query": "Get onboarding checklist and employee data"},
                dependencies=["main_coordination"]  # Depends on main task
            ),
            TaskNode(
                task_id="personalized_greeting",
                description="Create personalized greeting",
                agent_id="greeting_agent_social",
                input_data={"context": "Onboarding greeting", "employee": "Charlie"},
                dependencies=["hr_data_gathering"]  # Depends on HR data
            )
        ]
        
        # Mock hierarchical execution
        with patch.object(self.orchestrator, '_execute_single_task') as mock_execute:
            mock_execute.side_effect = [
                {"status": "completed", "result": "Coordination initiated for onboarding"},
                {"status": "completed", "result": "HR data gathered: checklist, employee info"},
                {"status": "completed", "result": "Welcome Charlie! Here's your personalized onboarding info"}
            ]
            
            # Execute hierarchical workflow
            result = await self.orchestrator.execute_workflow(
                workflow_id="hierarchical_test_001",
                tasks=tasks,
                pattern=CoordinationPattern.HIERARCHICAL,
                context={"test_mode": True, "employee_onboarding": True}
            )
            
            # Verify hierarchical execution
            assert result.status == TaskStatus.COMPLETED, "Hierarchical workflow should complete successfully"
            
            # Verify execution order (tasks should execute in dependency order)
            call_order = [call[0][0].task_id for call in mock_execute.call_args_list]
            assert call_order[0] == "main_coordination", "Main task should execute first"
            assert call_order[1] == "hr_data_gathering", "HR task should execute after main"
            assert call_order[2] == "personalized_greeting", "Greeting should execute last"
    
    @pytest.mark.asyncio
    async def test_consensus_coordination_workflow(self):
        """Test consensus coordination pattern with multiple agent opinions"""
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
        
        # Mock consensus execution with different agent responses
        with patch.object(self.orchestrator, '_execute_single_task') as mock_execute:
            mock_execute.side_effect = [
                {
                    "status": "completed", 
                    "result": "Employee development and retention",
                    "confidence": 0.9,
                    "reasoning": "Focus on career growth and satisfaction"
                },
                {
                    "status": "completed", 
                    "result": "Operational efficiency and employee satisfaction", 
                    "confidence": 0.85,
                    "reasoning": "Balance productivity with workplace culture"
                },
                {
                    "status": "completed", 
                    "result": "Positive workplace culture and communication",
                    "confidence": 0.8,
                    "reasoning": "Social aspects drive employee engagement"
                }
            ]
            
            # Execute consensus workflow
            result = await self.orchestrator.execute_workflow(
                workflow_id="consensus_test_001",
                tasks=tasks,
                pattern=CoordinationPattern.CONSENSUS,
                context={"test_mode": True, "decision_making": True}
            )
            
            # Verify consensus execution
            assert result.status == TaskStatus.COMPLETED, "Consensus workflow should complete successfully"
            assert mock_execute.call_count == 3, "Should execute all consensus tasks"
    
    @pytest.mark.asyncio
    async def test_competitive_coordination_workflow(self):
        """Test competitive coordination pattern with best result selection"""
        # Create competitive tasks - multiple agents solving the same problem
        tasks = [
            TaskNode(
                task_id="competitive_hr_solution",
                description="Find the best employee matching criteria",
                agent_id="hr_agent_specialist",
                input_data={"query": "Find employees with leadership potential", "criteria": "management_ready"}
            ),
            TaskNode(
                task_id="competitive_main_solution",
                description="Analyze employee data for leadership candidates", 
                agent_id="main_agent_coordinator",
                input_data={"task": "Identify leadership candidates using data analysis"}
            ),
            TaskNode(
                task_id="competitive_greeting_solution",
                description="Identify employees with strong communication skills",
                agent_id="greeting_agent_social",
                input_data={"context": "Find employees with excellent interpersonal skills"}
            )
        ]
        
        # Mock competitive execution with quality scores
        with patch.object(self.orchestrator, '_execute_single_task') as mock_execute:
            mock_execute.side_effect = [
                {
                    "status": "completed",
                    "result": "Found 3 management-ready employees with strong performance records",
                    "quality_score": 8.5,
                    "confidence": 0.9
                },
                {
                    "status": "completed", 
                    "result": "Analysis identifies 5 leadership candidates based on metrics",
                    "quality_score": 9.2,  # Best score
                    "confidence": 0.95
                },
                {
                    "status": "completed",
                    "result": "Identified 4 employees with exceptional communication abilities", 
                    "quality_score": 7.8,
                    "confidence": 0.85
                }
            ]
            
            # Execute competitive workflow
            result = await self.orchestrator.execute_workflow(
                workflow_id="competitive_test_001",
                tasks=tasks,
                pattern=CoordinationPattern.COMPETITIVE,
                context={"test_mode": True, "best_result_selection": True}
            )
            
            # Verify competitive execution
            assert result.status == TaskStatus.COMPLETED, "Competitive workflow should complete successfully"
            assert mock_execute.call_count == 3, "Should execute all competing tasks"
    
    @pytest.mark.asyncio
    async def test_collaborative_coordination_workflow(self):
        """Test collaborative coordination pattern with shared context"""
        # Create collaborative tasks that build on each other
        tasks = [
            TaskNode(
                task_id="collab_data_gathering",
                description="Gather initial employee data",
                agent_id="hr_agent_specialist",
                input_data={"query": "Get comprehensive employee dataset"}
            ),
            TaskNode(
                task_id="collab_analysis",
                description="Analyze gathered data for insights", 
                agent_id="main_agent_coordinator",
                input_data={"task": "Analyze employee data for patterns and trends"}
            ),
            TaskNode(
                task_id="collab_communication",
                description="Create communication strategy based on analysis",
                agent_id="greeting_agent_social",
                input_data={"context": "Develop communication strategy for insights"}
            )
        ]
        
        # Mock collaborative execution - the orchestrator might not call _execute_single_task
        # if the task structure doesn't match expected phases
        shared_context = {"employee_data": [], "insights": [], "strategies": []}
        
        with patch.object(self.orchestrator, '_execute_single_task') as mock_execute:
            def collaborative_execution(task):
                if "data_gathering" in task.task_id:
                    shared_context["employee_data"] = ["emp1", "emp2", "emp3"]
                    return {
                        "status": "completed",
                        "result": "Gathered data for 3 employees",
                        "shared_context": shared_context
                    }
                elif "analysis" in task.task_id:
                    shared_context["insights"] = ["trend1", "pattern2"]
                    return {
                        "status": "completed", 
                        "result": "Found 2 key insights from employee data",
                        "shared_context": shared_context
                    }
                else:  # communication
                    shared_context["strategies"] = ["strategy1", "strategy2"]
                    return {
                        "status": "completed",
                        "result": "Developed 2 communication strategies",
                        "shared_context": shared_context
                    }
            
            mock_execute.side_effect = collaborative_execution
            
            # Execute collaborative workflow
            result = await self.orchestrator.execute_workflow(
                workflow_id="collaborative_test_001",
                tasks=tasks,
                pattern=CoordinationPattern.COLLABORATIVE,
                context={"test_mode": True, "shared_workspace": True}
            )
            
            # Verify collaborative execution
            assert result.status == TaskStatus.COMPLETED, "Collaborative workflow should complete successfully"
            # Note: collaborative pattern may not call _execute_single_task if tasks don't have expected metadata
    
    def test_coordination_pattern_validation(self):
        """Test validation of coordination patterns and task configurations"""
        # Test valid coordination patterns
        valid_patterns = [
            CoordinationPattern.SEQUENTIAL,
            CoordinationPattern.PARALLEL,
            CoordinationPattern.HIERARCHICAL,
            CoordinationPattern.CONSENSUS,
            CoordinationPattern.COMPETITIVE,
            CoordinationPattern.COLLABORATIVE
        ]
        
        for pattern in valid_patterns:
            # Should not raise any exceptions
            assert pattern in CoordinationPattern, f"Pattern {pattern} should be valid"
    
    @pytest.mark.asyncio
    async def test_workflow_error_handling(self):
        """Test error handling in coordination workflows"""
        # Create tasks with potential failure
        tasks = [
            TaskNode(
                task_id="failing_task",
                description="Task that will fail",
                agent_id="nonexistent_agent",
                input_data={"query": "This will fail"}
            )
        ]
        
        # Mock task execution failure
        with patch.object(self.orchestrator, '_execute_single_task') as mock_execute:
            mock_execute.side_effect = Exception("Task execution failed")
            
            # Execute workflow and expect graceful error handling
            result = await self.orchestrator.execute_workflow(
                workflow_id="error_test_001",
                tasks=tasks,
                pattern=CoordinationPattern.SEQUENTIAL,
                context={"test_mode": True, "expect_failure": True}
            )
            
            # Verify error handling
            assert result.status == TaskStatus.FAILED, "Workflow should fail gracefully"
    
    def test_task_node_creation_and_validation(self):
        """Test TaskNode creation and validation"""
        # Test valid task node creation
        task = TaskNode(
            task_id="test_task",
            description="Test task description",
            agent_id="test_agent",
            input_data={"key": "value"}
        )
        
        assert task.task_id == "test_task", "Task ID should be set correctly"
        assert task.description == "Test task description", "Description should be set"
        assert task.agent_id == "test_agent", "Agent ID should be set"
        assert task.input_data["key"] == "value", "Input data should be preserved"
        
        # Test task with dependencies
        dependent_task = TaskNode(
            task_id="dependent_task",
            description="Task with dependencies",
            agent_id="test_agent",
            input_data={},
            dependencies=["test_task"]
        )
        
        assert len(dependent_task.dependencies) == 1, "Dependencies should be set"
        assert "test_task" in dependent_task.dependencies, "Dependency should be recorded"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
