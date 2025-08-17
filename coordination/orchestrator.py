#!/usr/bin/env python3
"""
Phase 7: Multi-Agent Coordination - Orchestrator
Advanced coordination engine for complex multi-agent workflows
"""

import asyncio
import json
import os
import sys
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from a2a.protocol import A2AMessage, A2AProtocol, AgentCapability, MessageType


class TaskStatus(Enum):
    """Task execution status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING_DEPENDENCIES = "waiting_dependencies"


class CoordinationPattern(Enum):
    """Multi-agent coordination patterns"""

    SEQUENTIAL = "sequential"  # Tasks executed in sequence
    PARALLEL = "parallel"  # Tasks executed simultaneously
    PIPELINE = "pipeline"  # Output of one feeds into next
    HIERARCHICAL = "hierarchical"  # Tree-like delegation structure
    CONSENSUS = "consensus"  # Agents vote/agree on decisions
    COMPETITIVE = "competitive"  # Best result wins
    COLLABORATIVE = "collaborative"  # Agents work together on shared task


@dataclass
class TaskNode:
    """Individual task in a coordination workflow"""

    task_id: str
    description: str
    agent_id: str
    input_data: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout: float = 60.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowResult:
    """Result of a multi-agent workflow execution"""

    workflow_id: str
    status: TaskStatus
    results: Dict[str, Any]
    execution_time: float
    task_results: Dict[str, TaskNode]
    coordination_pattern: CoordinationPattern
    summary: str
    metrics: Dict[str, Any] = field(default_factory=dict)


class MultiAgentOrchestrator:
    """
    Advanced multi-agent coordination orchestrator
    Manages complex workflows with multiple agents
    """

    def __init__(self, name: str = "MultiAgentOrchestrator"):
        self.name = name
        self.orchestrator_id = "coordination_orchestrator"
        self.endpoint = "http://localhost:8004"

        # A2A Protocol for agent communication
        self.a2a = A2AProtocol(
            agent_id=self.orchestrator_id,
            agent_name=self.name,
            endpoint=self.endpoint,
            secret_key=os.getenv("A2A_SECRET_KEY", "rag_a2a_mcp_secret"),
        )

        # Known agents in the system
        self.known_agents = {
            "hr_agent_specialist": "http://localhost:8002",
            "greeting_agent_social": "http://localhost:8003",
            "main_agent_coordinator": "http://localhost:8001",
        }

        # Active workflows
        self.active_workflows: Dict[str, Dict[str, TaskNode]] = {}
        self.workflow_results: Dict[str, WorkflowResult] = {}

        # Agent capabilities cache
        self.agent_capabilities: Dict[str, List[AgentCapability]] = {}

        # Coordination patterns
        self.coordination_handlers = {
            CoordinationPattern.SEQUENTIAL: self._execute_sequential,
            CoordinationPattern.PARALLEL: self._execute_parallel,
            CoordinationPattern.PIPELINE: self._execute_pipeline,
            CoordinationPattern.HIERARCHICAL: self._execute_hierarchical,
            CoordinationPattern.CONSENSUS: self._execute_consensus,
            CoordinationPattern.COMPETITIVE: self._execute_competitive,
            CoordinationPattern.COLLABORATIVE: self._execute_collaborative,
        }

    async def execute_workflow(
        self,
        workflow_id: str,
        tasks: List[TaskNode],
        pattern: CoordinationPattern,
        context: Dict[str, Any] = None,
    ) -> WorkflowResult:
        """Execute a multi-agent workflow with specified coordination pattern"""

        print(f"Orchestrator: Starting workflow '{workflow_id}' with {pattern.value} coordination")
        print(
            f"Tasks: {len(tasks)} tasks across {len(set(task.agent_id for task in tasks))} agents"
        )

        start_time = time.time()
        context = context or {}

        # Initialize workflow tracking
        self.active_workflows[workflow_id] = {task.task_id: task for task in tasks}

        try:
            # Execute based on coordination pattern
            handler = self.coordination_handlers[pattern]
            results = await handler(workflow_id, tasks, context)

            execution_time = time.time() - start_time

            # Create workflow result
            workflow_result = WorkflowResult(
                workflow_id=workflow_id,
                status=TaskStatus.COMPLETED,
                results=results,
                execution_time=execution_time,
                task_results=self.active_workflows[workflow_id],
                coordination_pattern=pattern,
                summary=self._generate_workflow_summary(workflow_id, results),
                metrics=self._calculate_workflow_metrics(workflow_id, execution_time),
            )

            self.workflow_results[workflow_id] = workflow_result

            print(f"SUCCESS: Workflow '{workflow_id}' completed in {execution_time:.2f}s")
            return workflow_result

        except Exception as e:
            execution_time = time.time() - start_time
            error_result = WorkflowResult(
                workflow_id=workflow_id,
                status=TaskStatus.FAILED,
                results={"error": str(e)},
                execution_time=execution_time,
                task_results=self.active_workflows[workflow_id],
                coordination_pattern=pattern,
                summary=f"Workflow failed: {str(e)}",
                metrics=self._calculate_workflow_metrics(workflow_id, execution_time),
            )

            self.workflow_results[workflow_id] = error_result
            print(f"Workflow '{workflow_id}' failed: {str(e)}")
            return error_result

    async def _execute_sequential(
        self, workflow_id: str, tasks: List[TaskNode], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute tasks sequentially, one after another"""
        results = {}

        for task in tasks:
            print(f"Sequential: Executing task '{task.task_id}' on agent '{task.agent_id}'")

            # Update context with previous results
            task.input_data.update({"previous_results": results, "context": context})

            task_result = await self._execute_single_task(task)
            results[task.task_id] = task_result

            # If task failed and it's critical, stop workflow
            if task.status == TaskStatus.FAILED and task.metadata.get("critical", False):
                raise Exception(f"Critical task '{task.task_id}' failed: {task.error}")

        return results

    async def _execute_parallel(
        self, workflow_id: str, tasks: List[TaskNode], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute tasks in parallel across multiple agents"""
        print(f"Parallel: Executing {len(tasks)} tasks simultaneously")

        # Prepare all tasks
        for task in tasks:
            task.input_data.update({"context": context})

        # Execute all tasks concurrently
        task_coroutines = [self._execute_single_task(task) for task in tasks]
        task_results = await asyncio.gather(*task_coroutines, return_exceptions=True)

        # Collect results
        results = {}
        for task, result in zip(tasks, task_results):
            if isinstance(result, Exception):
                task.status = TaskStatus.FAILED
                task.error = str(result)
                results[task.task_id] = {"error": str(result)}
            else:
                results[task.task_id] = result

        return results

    async def _execute_pipeline(
        self, workflow_id: str, tasks: List[TaskNode], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute tasks in pipeline fashion - output feeds into next input"""
        results = {}
        pipeline_data = context.copy()

        for i, task in enumerate(tasks):
            print(
                f"Pipeline: Stage {i+1}/{len(tasks)} - Task '{task.task_id}' on agent '{task.agent_id}'"
            )

            # Feed pipeline data into current task
            task.input_data.update(
                {"pipeline_data": pipeline_data, "stage_number": i + 1, "total_stages": len(tasks)}
            )

            task_result = await self._execute_single_task(task)
            results[task.task_id] = task_result

            # Update pipeline data with result
            if task.status == TaskStatus.COMPLETED and isinstance(task_result, dict):
                pipeline_data.update(task_result)

            # Stop pipeline if task failed
            if task.status == TaskStatus.FAILED:
                raise Exception(f"Pipeline broken at stage {i+1}: {task.error}")

        return results

    async def _execute_hierarchical(
        self, workflow_id: str, tasks: List[TaskNode], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute tasks in hierarchical tree structure based on dependencies"""
        results = {}
        completed_tasks = set()

        # Build dependency graph
        task_map = {task.task_id: task for task in tasks}

        while len(completed_tasks) < len(tasks):
            # Find tasks ready to execute (dependencies met)
            ready_tasks = []
            for task in tasks:
                if task.task_id not in completed_tasks and all(
                    dep in completed_tasks for dep in task.dependencies
                ):
                    ready_tasks.append(task)

            if not ready_tasks:
                raise Exception("Circular dependency or unresolvable dependencies detected")

            print(f"Hierarchical: Executing {len(ready_tasks)} tasks with satisfied dependencies")

            # Execute ready tasks in parallel
            for task in ready_tasks:
                # Gather dependency results
                dep_results = {dep: results.get(dep) for dep in task.dependencies}
                task.input_data.update({"dependency_results": dep_results, "context": context})

            # Execute tasks
            task_coroutines = [self._execute_single_task(task) for task in ready_tasks]
            task_results = await asyncio.gather(*task_coroutines, return_exceptions=True)

            # Update results and completed tasks
            for task, result in zip(ready_tasks, task_results):
                if isinstance(result, Exception):
                    task.status = TaskStatus.FAILED
                    task.error = str(result)
                    results[task.task_id] = {"error": str(result)}
                else:
                    results[task.task_id] = result
                completed_tasks.add(task.task_id)

        return results

    async def _execute_consensus(
        self, workflow_id: str, tasks: List[TaskNode], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute tasks and reach consensus on the result"""
        print(f"Consensus: Gathering opinions from {len(tasks)} agents")

        # Execute all tasks (same query to different agents)
        for task in tasks:
            task.input_data.update({"context": context, "consensus_mode": True})

        task_coroutines = [self._execute_single_task(task) for task in tasks]
        task_results = await asyncio.gather(*task_coroutines, return_exceptions=True)

        # Collect agent responses
        agent_responses = {}
        for task, result in zip(tasks, task_results):
            if not isinstance(result, Exception):
                agent_responses[task.agent_id] = result

        # Determine consensus (simplified - could be more sophisticated)
        consensus_result = self._determine_consensus(agent_responses)

        return {
            "consensus_result": consensus_result,
            "individual_responses": agent_responses,
            "consensus_method": "majority_vote",
        }

    async def _execute_competitive(
        self, workflow_id: str, tasks: List[TaskNode], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute tasks competitively - best result wins"""
        print(f"Competitive: Racing {len(tasks)} agents for best result")

        # Execute all tasks with same input
        for task in tasks:
            task.input_data.update({"context": context, "competitive_mode": True})

        task_coroutines = [self._execute_single_task(task) for task in tasks]
        task_results = await asyncio.gather(*task_coroutines, return_exceptions=True)

        # Evaluate results and pick winner
        agent_results = {}
        for task, result in zip(tasks, task_results):
            if not isinstance(result, Exception):
                agent_results[task.agent_id] = {
                    "result": result,
                    "execution_time": (
                        task.end_time - task.start_time if task.end_time and task.start_time else 0
                    ),
                    "quality_score": self._evaluate_result_quality(result),
                }

        winner = self._determine_winner(agent_results)

        return {
            "winner": winner,
            "winning_result": agent_results[winner]["result"] if winner else None,
            "all_results": agent_results,
            "competition_method": "quality_and_speed",
        }

    async def _execute_collaborative(
        self, workflow_id: str, tasks: List[TaskNode], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute tasks collaboratively - agents work together"""
        print(f"Collaborative: {len(tasks)} agents working together")

        # Phase 1: Information gathering
        gather_tasks = [task for task in tasks if task.metadata.get("phase") == "gather"]
        if gather_tasks:
            print("Phase 1: Information gathering")
            gathered_info = {}
            for task in gather_tasks:
                task.input_data.update({"context": context, "phase": "gather"})
                result = await self._execute_single_task(task)
                gathered_info[task.agent_id] = result
        else:
            gathered_info = {}

        # Phase 2: Collaborative processing
        process_tasks = [task for task in tasks if task.metadata.get("phase") == "process"]
        if process_tasks:
            print("Phase 2: Collaborative processing")
            for task in process_tasks:
                task.input_data.update(
                    {"context": context, "gathered_info": gathered_info, "phase": "process"}
                )

            process_coroutines = [self._execute_single_task(task) for task in process_tasks]
            process_results = await asyncio.gather(*process_coroutines, return_exceptions=True)

            collaborative_results = {}
            for task, result in zip(process_tasks, process_results):
                if not isinstance(result, Exception):
                    collaborative_results[task.agent_id] = result
        else:
            collaborative_results = {}

        # Phase 3: Synthesis
        final_result = self._synthesize_collaborative_results(gathered_info, collaborative_results)

        return {
            "gathered_info": gathered_info,
            "collaborative_results": collaborative_results,
            "synthesized_result": final_result,
        }

    async def _execute_single_task(self, task: TaskNode) -> Any:
        """Execute a single task on a specific agent"""
        task.start_time = time.time()
        task.status = TaskStatus.RUNNING

        try:
            # Create delegation message
            delegation_message = self.a2a.create_message(
                MessageType.DELEGATION_REQUEST,
                task.agent_id,
                {
                    "task": task.description,
                    "input_data": task.input_data,
                    "task_id": task.task_id,
                    "metadata": task.metadata,
                },
            )

            # Send to agent
            agent_endpoint = self.known_agents.get(task.agent_id)
            if not agent_endpoint:
                raise Exception(f"Unknown agent: {task.agent_id}")

            response = await self._send_delegation_message(agent_endpoint, delegation_message)

            # Check if response is a valid A2A delegation response
            if (
                response.get("message_type") == "delegation_response"
                and response.get("payload", {}).get("status") == "success"
            ):
                task.status = TaskStatus.COMPLETED
                task.result = response.get("payload", {}).get("result")
                task.end_time = time.time()
                return task.result
            else:
                error_msg = response.get("payload", {}).get("error") or response.get(
                    "error", "Task execution failed"
                )
                raise Exception(error_msg)

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.end_time = time.time()

            # Retry logic
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                print(
                    f"WARNING: Task '{task.task_id}' failed, retrying ({task.retry_count}/{task.max_retries})"
                )
                await asyncio.sleep(1)  # Brief delay before retry
                return await self._execute_single_task(task)
            else:
                raise e

    async def _send_delegation_message(self, endpoint: str, message: A2AMessage) -> Dict[str, Any]:
        """Send delegation message to agent"""
        import aiohttp

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{endpoint}/a2a",
                    json=message.to_dict(),
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    return await response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _determine_consensus(self, agent_responses: Dict[str, Any]) -> Any:
        """Determine consensus from multiple agent responses"""
        # Simple majority-based consensus (can be enhanced)
        if not agent_responses:
            return None

        # For text responses, find most common
        response_counts = {}
        for agent_id, response in agent_responses.items():
            response_str = str(response)
            response_counts[response_str] = response_counts.get(response_str, 0) + 1

        # Return most frequent response
        if response_counts:
            consensus = max(response_counts.items(), key=lambda x: x[1])[0]
            return consensus

        return list(agent_responses.values())[0]

    def _determine_winner(self, agent_results: Dict[str, Dict[str, Any]]) -> Optional[str]:
        """Determine winner in competitive execution"""
        if not agent_results:
            return None

        # Score based on quality and speed
        best_score = -1
        winner = None

        for agent_id, data in agent_results.items():
            quality = data.get("quality_score", 0)
            speed_bonus = max(0, 10 - data.get("execution_time", 10))  # Bonus for speed
            total_score = quality + (speed_bonus * 0.1)

            if total_score > best_score:
                best_score = total_score
                winner = agent_id

        return winner

    def _evaluate_result_quality(self, result: Any) -> float:
        """Evaluate quality of a result (0-10 scale)"""
        # Simple heuristic - can be enhanced with ML models
        if not result:
            return 0.0

        result_str = str(result)

        # Base score on length and content richness
        length_score = min(5.0, len(result_str) / 100)

        # Bonus for structured data
        structure_bonus = 2.0 if isinstance(result, dict) else 0.0

        # Bonus for detailed responses
        detail_bonus = 2.0 if len(result_str) > 200 else 1.0

        return min(10.0, length_score + structure_bonus + detail_bonus)

    def _synthesize_collaborative_results(
        self, gathered_info: Dict[str, Any], processed_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Synthesize results from collaborative execution"""
        return {
            "summary": "Collaborative workflow completed",
            "information_sources": len(gathered_info),
            "processing_agents": len(processed_results),
            "combined_insights": {"gathered": gathered_info, "processed": processed_results},
            "synthesis_timestamp": time.time(),
        }

    def _generate_workflow_summary(self, workflow_id: str, results: Dict[str, Any]) -> str:
        """Generate human-readable workflow summary"""
        workflow = self.active_workflows.get(workflow_id, {})

        total_tasks = len(workflow)
        completed_tasks = sum(
            1 for task in workflow.values() if task.status == TaskStatus.COMPLETED
        )
        failed_tasks = sum(1 for task in workflow.values() if task.status == TaskStatus.FAILED)

        agents_involved = set(task.agent_id for task in workflow.values())

        summary = f"Workflow '{workflow_id}': {completed_tasks}/{total_tasks} tasks completed"
        if failed_tasks > 0:
            summary += f", {failed_tasks} failed"
        summary += f". Agents involved: {', '.join(agents_involved)}"

        return summary

    def _calculate_workflow_metrics(
        self, workflow_id: str, execution_time: float
    ) -> Dict[str, Any]:
        """Calculate workflow performance metrics"""
        workflow = self.active_workflows.get(workflow_id, {})

        task_times = [
            task.end_time - task.start_time
            for task in workflow.values()
            if task.start_time and task.end_time
        ]

        return {
            "total_execution_time": execution_time,
            "average_task_time": sum(task_times) / len(task_times) if task_times else 0,
            "max_task_time": max(task_times) if task_times else 0,
            "min_task_time": min(task_times) if task_times else 0,
            "task_count": len(workflow),
            "agent_count": len(set(task.agent_id for task in workflow.values())),
            "success_rate": (
                sum(1 for task in workflow.values() if task.status == TaskStatus.COMPLETED)
                / len(workflow)
                if workflow
                else 0
            ),
        }


if __name__ == "__main__":
    print("Multi-Agent Orchestrator - Phase 7")
    print("=" * 50)
    print("Advanced coordination patterns available:")
    print("  Sequential - Tasks in order")
    print("  Parallel - Simultaneous execution")
    print("  Pipeline - Data flows through stages")
    print("  Hierarchical - Dependency-based execution")
    print("  Consensus - Agents agree on result")
    print("  Competitive - Best result wins")
    print("  Collaborative - Agents work together")
    print()

    orchestrator = MultiAgentOrchestrator()
    print(f"Orchestrator '{orchestrator.name}' initialized")
    print(f"Known agents: {list(orchestrator.known_agents.keys())}")
