#!/usr/bin/env python3
"""
Phase 7: Multi-Agent Coordination - Workflow Examples
Practical examples of different coordination patterns
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from coordination.orchestrator import (
    MultiAgentOrchestrator, TaskNode, CoordinationPattern, TaskStatus
)

class WorkflowExamples:
    """Collection of practical multi-agent workflow examples"""
    
    def __init__(self):
        self.orchestrator = MultiAgentOrchestrator()
    
    async def example_1_sequential_employee_onboarding(self):
        """
        Sequential workflow: New employee onboarding process
        HR -> Greeting -> HR (final setup)
        """
        print("🔄 Example 1: Sequential Employee Onboarding")
        print("-" * 50)
        
        tasks = [
            TaskNode(
                task_id="check_employee_records",
                description="Check if new employee John Doe exists in system",
                agent_id="hr_agent",
                input_data={"employee_name": "John Doe", "action": "search"},
                metadata={"critical": True}
            ),
            TaskNode(
                task_id="generate_welcome_message",
                description="Generate personalized welcome message for new employee",
                agent_id="greeting_agent",
                input_data={"employee_name": "John Doe", "occasion": "onboarding"},
                metadata={"critical": False}
            ),
            TaskNode(
                task_id="finalize_onboarding",
                description="Get final onboarding checklist and requirements",
                agent_id="hr_agent",
                input_data={"employee_name": "John Doe", "action": "onboarding_checklist"},
                metadata={"critical": True}
            )
        ]
        
        result = await self.orchestrator.execute_workflow(
            workflow_id="employee_onboarding_001",
            tasks=tasks,
            pattern=CoordinationPattern.SEQUENTIAL,
            context={"department": "Engineering", "start_date": "2025-07-01"}
        )
        
        return result
    
    async def example_2_parallel_multi_department_analysis(self):
        """
        Parallel workflow: Analyze multiple departments simultaneously
        HR analyzes different departments in parallel
        """
        print("⚡ Example 2: Parallel Multi-Department Analysis")
        print("-" * 50)
        
        departments = ["Engineering", "Marketing", "Sales", "Data Science"]
        tasks = []
        
        for dept in departments:
            tasks.append(TaskNode(
                task_id=f"analyze_{dept.lower().replace(' ', '_')}",
                description=f"Analyze {dept} department metrics and team structure",
                agent_id="hr_agent",
                input_data={"department": dept, "analysis_type": "comprehensive"},
                metadata={"department": dept}
            ))
        
        result = await self.orchestrator.execute_workflow(
            workflow_id="department_analysis_parallel",
            tasks=tasks,
            pattern=CoordinationPattern.PARALLEL,
            context={"analysis_date": "2025-06-29", "quarterly_review": True}
        )
        
        return result
    
    async def example_3_pipeline_employee_report(self):
        """
        Pipeline workflow: Employee data flows through processing stages
        HR gets data -> Main agent processes -> Greeting agent formats
        """
        print("🔗 Example 3: Pipeline Employee Report Generation")
        print("-" * 50)
        
        tasks = [
            TaskNode(
                task_id="gather_employee_data",
                description="Get comprehensive employee directory information",
                agent_id="hr_agent",
                input_data={"query": "List all employees with detailed information"},
                metadata={"stage": "data_gathering"}
            ),
            TaskNode(
                task_id="process_analytics",
                description="Process and analyze the employee data for insights",
                agent_id="main_agent",
                input_data={"task": "Analyze employee data for key insights and patterns"},
                metadata={"stage": "processing"}
            ),
            TaskNode(
                task_id="format_presentation",
                description="Format the analysis into a friendly, presentable report",
                agent_id="greeting_agent",
                input_data={"task": "Create a friendly summary of employee analysis"},
                metadata={"stage": "formatting"}
            )
        ]
        
        result = await self.orchestrator.execute_workflow(
            workflow_id="employee_report_pipeline",
            tasks=tasks,
            pattern=CoordinationPattern.PIPELINE,
            context={"report_type": "quarterly", "audience": "management"}
        )
        
        return result
    
    async def example_4_hierarchical_project_planning(self):
        """
        Hierarchical workflow: Project planning with dependencies
        Overview -> Detailed analysis -> Team assignment
        """
        print("🌳 Example 4: Hierarchical Project Planning")
        print("-" * 50)
        
        tasks = [
            TaskNode(
                task_id="company_overview",
                description="Get overall company structure and employee overview",
                agent_id="hr_agent",
                input_data={"query": "Company overview and analytics"},
                dependencies=[],  # No dependencies - can start immediately
                metadata={"priority": "high"}
            ),
            TaskNode(
                task_id="engineering_team_analysis",
                description="Detailed analysis of Engineering department",
                agent_id="hr_agent",
                input_data={"department": "Engineering", "analysis_type": "detailed"},
                dependencies=["company_overview"],  # Depends on overview
                metadata={"priority": "medium"}
            ),
            TaskNode(
                task_id="project_team_greeting",
                description="Generate team introduction and project kickoff message",
                agent_id="greeting_agent",
                input_data={"occasion": "project_kickoff", "team": "Engineering"},
                dependencies=["engineering_team_analysis"],  # Depends on team analysis
                metadata={"priority": "low"}
            ),
            TaskNode(
                task_id="coordination_summary",
                description="Summarize the project planning results and next steps",
                agent_id="main_agent",
                input_data={"task": "Summarize project planning outcomes"},
                dependencies=["engineering_team_analysis", "project_team_greeting"],  # Depends on both
                metadata={"priority": "high"}
            )
        ]
        
        result = await self.orchestrator.execute_workflow(
            workflow_id="project_planning_hierarchical",
            tasks=tasks,
            pattern=CoordinationPattern.HIERARCHICAL,
            context={"project_name": "Q3 Platform Enhancement", "timeline": "12 weeks"}
        )
        
        return result
    
    async def example_5_consensus_decision_making(self):
        """
        Consensus workflow: Multiple agents provide opinions on a decision
        All agents analyze the same question and reach consensus
        """
        print("🤝 Example 5: Consensus Decision Making")
        print("-" * 50)
        
        decision_question = "Should we hire more employees for the Engineering team?"
        
        tasks = [
            TaskNode(
                task_id="hr_perspective",
                description=decision_question,
                agent_id="hr_agent",
                input_data={
                    "query": "Engineering team analysis for hiring decision",
                    "decision_context": decision_question
                },
                metadata={"perspective": "hr_specialist"}
            ),
            TaskNode(
                task_id="greeting_perspective",
                description=decision_question,
                agent_id="greeting_agent",
                input_data={
                    "query": "Team culture and onboarding considerations for new hires",
                    "decision_context": decision_question
                },
                metadata={"perspective": "social_specialist"}
            ),
            TaskNode(
                task_id="main_perspective",
                description=decision_question,
                agent_id="main_agent",
                input_data={
                    "query": "Overall strategic analysis of Engineering team expansion",
                    "decision_context": decision_question
                },
                metadata={"perspective": "general_coordinator"}
            )
        ]
        
        result = await self.orchestrator.execute_workflow(
            workflow_id="hiring_decision_consensus",
            tasks=tasks,
            pattern=CoordinationPattern.CONSENSUS,
            context={"budget_cycle": "Q3", "growth_target": "20%"}
        )
        
        return result
    
    async def example_6_competitive_best_answer(self):
        """
        Competitive workflow: Agents compete to provide the best answer
        Multiple agents try to answer the same question, best result wins
        """
        print("🏆 Example 6: Competitive Best Answer")
        print("-" * 50)
        
        challenge_question = "What are the key metrics and insights about our employee base?"
        
        tasks = [
            TaskNode(
                task_id="hr_solution",
                description=challenge_question,
                agent_id="hr_agent",
                input_data={"query": "Comprehensive HR analytics and employee insights"},
                metadata={"approach": "specialist_analysis"}
            ),
            TaskNode(
                task_id="main_solution",
                description=challenge_question,
                agent_id="main_agent",
                input_data={"query": "Employee base analysis and key business metrics"},
                metadata={"approach": "general_analysis"}
            )
        ]
        
        result = await self.orchestrator.execute_workflow(
            workflow_id="best_insights_competition",
            tasks=tasks,
            pattern=CoordinationPattern.COMPETITIVE,
            context={"evaluation_criteria": ["completeness", "accuracy", "actionability"]}
        )
        
        return result
    
    async def example_7_collaborative_comprehensive_report(self):
        """
        Collaborative workflow: Agents work together on different aspects
        Gather info -> Process collaboratively -> Synthesize results
        """
        print("👥 Example 7: Collaborative Comprehensive Report")
        print("-" * 50)
        
        # Phase 1: Information gathering
        gather_tasks = [
            TaskNode(
                task_id="gather_hr_data",
                description="Gather comprehensive HR and employee data",
                agent_id="hr_agent",
                input_data={"query": "Complete employee directory and analytics"},
                metadata={"phase": "gather", "data_type": "hr_metrics"}
            )
        ]
        
        # Phase 2: Collaborative processing
        process_tasks = [
            TaskNode(
                task_id="process_business_insights",
                description="Extract business insights from gathered data",
                agent_id="main_agent",
                input_data={"task": "Analyze gathered data for business insights"},
                metadata={"phase": "process", "focus": "business_value"}
            ),
            TaskNode(
                task_id="process_team_dynamics",
                description="Analyze team culture and social aspects",
                agent_id="greeting_agent",
                input_data={"task": "Analyze team social dynamics and culture"},
                metadata={"phase": "process", "focus": "team_culture"}
            )
        ]
        
        all_tasks = gather_tasks + process_tasks
        
        result = await self.orchestrator.execute_workflow(
            workflow_id="collaborative_company_report",
            tasks=all_tasks,
            pattern=CoordinationPattern.COLLABORATIVE,
            context={"report_scope": "comprehensive", "stakeholders": ["management", "hr", "team_leads"]}
        )
        
        return result
    
    async def run_all_examples(self):
        """Run all workflow examples"""
        print("🎭 Multi-Agent Coordination Examples")
        print("=" * 60)
        print("Running 7 different coordination patterns...\n")
        
        examples = [
            self.example_1_sequential_employee_onboarding,
            self.example_2_parallel_multi_department_analysis,
            self.example_3_pipeline_employee_report,
            self.example_4_hierarchical_project_planning,
            self.example_5_consensus_decision_making,
            self.example_6_competitive_best_answer,
            self.example_7_collaborative_comprehensive_report
        ]
        
        results = []
        for i, example in enumerate(examples, 1):
            print(f"\n{'='*60}")
            print(f"RUNNING EXAMPLE {i}/7")
            print('='*60)
            
            try:
                result = await example()
                results.append(result)
                
                print(f"\n✅ Example {i} completed successfully!")
                print(f"📊 Status: {result.status.value}")
                print(f"⏱️ Execution time: {result.execution_time:.2f}s")
                print(f"📋 Summary: {result.summary}")
                
                if result.metrics:
                    print(f"📈 Success rate: {result.metrics['success_rate']:.1%}")
                    print(f"🎯 Agents involved: {result.metrics['agent_count']}")
                
            except Exception as e:
                print(f"❌ Example {i} failed: {str(e)}")
                results.append(None)
        
        # Final summary
        print(f"\n{'='*60}")
        print("COORDINATION EXAMPLES SUMMARY")
        print('='*60)
        
        successful = sum(1 for r in results if r and r.status == TaskStatus.COMPLETED)
        print(f"✅ Successful workflows: {successful}/{len(examples)}")
        print(f"📊 Success rate: {successful/len(examples):.1%}")
        
        if successful > 0:
            avg_time = sum(r.execution_time for r in results if r and r.status == TaskStatus.COMPLETED) / successful
            print(f"⏱️ Average execution time: {avg_time:.2f}s")
        
        print("\n🎉 Phase 7 Multi-Agent Coordination demonstration complete!")
        
        return results

async def main():
    """Main execution function"""
    examples = WorkflowExamples()
    await examples.run_all_examples()

if __name__ == "__main__":
    asyncio.run(main())
