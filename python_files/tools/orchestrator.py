# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "google-genai>=1.0.0",
#     "pydantic>=2.0.0",
#     "rich>=13.0.0",
# ]
# ///
"""
Agent Orchestrator

High-level workflow manager for complex multi-agent patterns.
Provides pre-built workflows and custom orchestration capabilities.

Usage:
    uv run orchestrator.py plan-and-execute --goal "Build a REST API"
    uv run orchestrator.py research-then-code --research "OAuth best practices" --task "Implement OAuth"
    uv run orchestrator.py map-reduce --files "*.py" --analysis "security audit"
"""

from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import Optional, Literal, Callable, Any
from enum import Enum
import asyncio
import argparse
import json
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.tree import Tree

# Import our tools
from .agent_fork import AgentForker, ForkConfig, AgentType, ForkResult, SwarmResult
from .context_summarizer import ContextSummarizer, ConversationHistory, ConversationTurn
from .agent_tools_integration import AgentToolsManager

# Logging setup
from .logging_config import get_logger, log_api_call, log_api_response, log_workflow_step, log_error, ensure_logging_setup
logger = get_logger('orchestrator')

console = Console()


class WorkflowStep(BaseModel):
    """A single step in an orchestrated workflow"""
    step_id: str
    name: str
    description: str
    agent_type: AgentType
    task: str
    depends_on: list[str] = Field(default_factory=list)
    status: Literal["pending", "running", "completed", "failed", "skipped"] = "pending"
    result: Optional[ForkResult] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class WorkflowPlan(BaseModel):
    """A complete workflow plan"""
    plan_id: str
    goal: str
    steps: list[WorkflowStep]
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    status: Literal["planned", "running", "completed", "failed"] = "planned"
    final_result: Optional[str] = None


class OrchestratorConfig(BaseModel):
    """Configuration for the orchestrator"""
    max_planning_steps: int = 10
    max_retries: int = 2
    thinking_budget_planning: int = 4096
    thinking_budget_execution: int = 2048
    parallel_execution: bool = True
    auto_consolidate: bool = True


class AgentOrchestrator:
    """
    High-level orchestrator for complex multi-agent workflows.
    
    Provides:
    - Plan-and-execute workflows
    - Research-then-code patterns
    - Map-reduce for batch processing
    - Custom workflow definitions
    - Automatic retry and error handling
    """
    
    def __init__(self, config: Optional[OrchestratorConfig] = None, api_key: Optional[str] = None):
        self.config = config or OrchestratorConfig()
        ensure_logging_setup()
        
        logger.info("Initializing AgentOrchestrator")
        logger.debug(f"Config: max_steps={self.config.max_planning_steps}, parallel={self.config.parallel_execution}")
        
        import os
        key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        
        if not key:
            logger.error("No API key found - GEMINI_API_KEY not set")
            raise ValueError(
                "GEMINI_API_KEY not set. Export it: export GEMINI_API_KEY='your-key'"
            )
        
        self.client = genai.Client(api_key=key)
        self.tools_manager = AgentToolsManager(workspace_root="./homease-ai-new")
        self.tools_manager.get_tool_declarations()
        # Pass tools_manager to AgentForker so it can execute file operations
        self.forker = AgentForker(api_key=key, tools_manager=self.tools_manager)
        self.summarizer = ContextSummarizer(api_key=key)
        self._workflow_counter = 0
        logger.info("AgentOrchestrator initialized successfully")
    
    def _generate_workflow_id(self) -> str:
        self._workflow_counter += 1
        return f"wf_{datetime.now().strftime('%H%M%S')}_{self._workflow_counter:03d}"
    
    async def plan_and_execute(
        self,
        goal: str,
        context: Optional[str] = None,
        max_steps: Optional[int] = None
    ) -> WorkflowPlan:
        """
        Plan a series of steps to achieve a goal, then execute them.
        
        This is the core agentic workflow pattern:
        1. Analyze the goal
        2. Generate a plan with discrete steps
        3. Execute each step (potentially in parallel)
        4. Consolidate results
        """
        workflow_id = self._generate_workflow_id()
        max_steps = max_steps or self.config.max_planning_steps
        
        logger.info(f"Starting plan_and_execute workflow {workflow_id}")
        logger.info(f"Goal: {goal[:200]}..." if len(goal) > 200 else f"Goal: {goal}")
        logger.debug(f"Context provided: {len(context) if context else 0} chars")
        
        console.print(Panel(
            f"[bold cyan]Goal:[/bold cyan] {goal}\n"
            f"[dim]Planning up to {max_steps} steps...[/dim]",
            title=f"🎯 Plan & Execute: {workflow_id}"
        ))
        
        # Step 1: Generate the plan
        plan_prompt = f"""You are a planning agent. Create a step-by-step plan to achieve this goal.

GOAL: {goal}

{f"CONTEXT: {context}" if context else ""}

Create a JSON plan with this structure:
{{
    "analysis": "Brief analysis of the goal and approach",
    "steps": [
        {{
            "step_id": "step_1",
            "name": "Short name",
            "description": "What this step does",
            "agent_type": "code|research|analysis|creative|general",
            "task": "The specific task for the agent",
            "depends_on": []  // list of step_ids this depends on
        }}
    ]
}}

Rules:
- Maximum {max_steps} steps
- Each step should be atomic and achievable
- Use appropriate agent_type for each step
- Identify dependencies between steps
- Steps with no dependencies can run in parallel
- Be specific in task descriptions

Return only valid JSON."""

        logger.debug(f"Generating plan with model gemini-2.5-pro")
        log_api_call(logger, "gemini-2.5-pro", plan_prompt, workflow_id=workflow_id, action="planning")

        plan_response = self.client.models.generate_content(
            model="gemini-2.5-pro",
            contents=plan_prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(
                    thinking_budget=self.config.thinking_budget_planning
                ),
                response_mime_type="application/json"
            )
        )
        
        log_api_response(logger, "gemini-2.5-pro", "success", workflow_id=workflow_id)
        
        try:
            plan_data = json.loads(plan_response.text)
            logger.info(f"Plan parsed successfully: {len(plan_data.get('steps', []))} steps")
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse plan JSON directly: {e}")
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', plan_response.text, re.DOTALL)
            if json_match:
                plan_data = json.loads(json_match.group())
                logger.info(f"Plan extracted from response: {len(plan_data.get('steps', []))} steps")
            else:
                logger.error("Failed to extract plan JSON from response")
                raise ValueError("Failed to parse plan JSON")
        
        # Build workflow plan
        steps = [
            WorkflowStep(
                step_id=s["step_id"],
                name=s["name"],
                description=s["description"],
                agent_type=AgentType(s["agent_type"]),
                task=s["task"],
                depends_on=s.get("depends_on", [])
            )
            for s in plan_data["steps"]
        ]
        
        workflow = WorkflowPlan(
            plan_id=workflow_id,
            goal=goal,
            steps=steps
        )
        
        # Display the plan
        tree = Tree(f"[bold]Plan: {workflow_id}[/bold]")
        for step in steps:
            deps = f" [dim](depends: {', '.join(step.depends_on)})[/dim]" if step.depends_on else ""
            tree.add(f"[{step.agent_type.value}] {step.name}{deps}")
            logger.debug(f"Step {step.step_id}: {step.name} (type={step.agent_type.value}, deps={step.depends_on})")
        console.print(tree)
        
        # Step 2: Execute the plan
        workflow.status = "running"
        logger.info(f"Executing workflow {workflow_id} ({'parallel' if self.config.parallel_execution else 'sequential'} mode)")
        
        if self.config.parallel_execution:
            await self._execute_parallel(workflow, context)
        else:
            await self._execute_sequential(workflow, context)
        
        # Step 3: Consolidate results
        if self.config.auto_consolidate:
            workflow.final_result = await self._consolidate_results(workflow)
        
        workflow.status = "completed" if all(
            s.status == "completed" for s in workflow.steps
        ) else "failed"
        
        completed = sum(1 for s in workflow.steps if s.status == "completed")
        failed = sum(1 for s in workflow.steps if s.status == "failed")
        logger.info(f"Workflow {workflow_id} {workflow.status}: {completed} completed, {failed} failed")
        
        return workflow
    
    async def _execute_sequential(self, workflow: WorkflowPlan, context: Optional[str]):
        """Execute steps sequentially"""
        logger.info(f"Starting sequential execution for {len(workflow.steps)} steps")
        results_context = context or ""
        
        for step in workflow.steps:
            step.status = "running"
            step.started_at = datetime.now().isoformat()
            
            # Add previous results to context
            task_with_context = f"{step.task}\n\nPrevious results:\n{results_context}" if results_context else step.task
            
            result = self.forker.fork(ForkConfig(
                task=task_with_context,
                agent_type=step.agent_type,
                context_summary=context
            ))
            
            step.result = result
            step.status = "completed" if result.status == "success" else "failed"
            step.completed_at = datetime.now().isoformat()
            
            log_workflow_step(logger, workflow.plan_id, step.step_id, step.status, 
                              name=step.name, agent_type=step.agent_type.value)
            
            # Accumulate context for next steps
            if result.status == "success":
                results_context += f"\n\n## {step.name}\n{result.response[:1000]}"
            
            console.print(f"[{'green' if step.status == 'completed' else 'red'}]"
                         f"{'✓' if step.status == 'completed' else '✗'} {step.name}[/]")
    
    async def _execute_parallel(self, workflow: WorkflowPlan, context: Optional[str]):
        """Execute steps in parallel where dependencies allow"""
        logger.info(f"Starting parallel execution for {len(workflow.steps)} steps")
        completed_steps: dict[str, ForkResult] = {}
        
        while True:
            # Find steps that can run (dependencies met)
            ready_steps = [
                s for s in workflow.steps
                if s.status == "pending" and all(
                    dep in completed_steps for dep in s.depends_on
                )
            ]
            
            if not ready_steps:
                # Check if we're done or stuck
                pending = [s for s in workflow.steps if s.status == "pending"]
                if not pending:
                    logger.info(f"All steps completed for workflow {workflow.plan_id}")
                    break
                else:
                    logger.error(f"Workflow stuck - unresolvable dependencies: {[s.step_id for s in pending]}")
                    console.print("[red]Workflow stuck - unresolvable dependencies[/red]")
                    break
            
            logger.info(f"Running {len(ready_steps)} parallel steps: {[s.step_id for s in ready_steps]}")
            console.print(f"[cyan]Running {len(ready_steps)} parallel steps...[/cyan]")
            
            # Execute ready steps in parallel
            async def run_step(step: WorkflowStep):
                step.status = "running"
                step.started_at = datetime.now().isoformat()
                
                # Build context from dependencies
                dep_context = "\n".join(
                    f"## {dep}\n{completed_steps[dep].response[:500]}"
                    for dep in step.depends_on
                    if dep in completed_steps
                )
                
                task_with_deps = step.task
                if dep_context:
                    task_with_deps = f"{step.task}\n\nContext from previous steps:\n{dep_context}"
                
                result = await self.forker.fork_async(ForkConfig(
                    task=task_with_deps,
                    agent_type=step.agent_type,
                    context_summary=context
                ))
                
                step.result = result
                step.status = "completed" if result.status == "success" else "failed"
                step.completed_at = datetime.now().isoformat()
                
                return step.step_id, result
            
            # Run all ready steps
            results = await asyncio.gather(*[run_step(s) for s in ready_steps])
            
            # Update completed steps
            for step_id, result in results:
                completed_steps[step_id] = result
                status_icon = "✓" if result.status == "success" else "✗"
                color = "green" if result.status == "success" else "red"
                step_name = next(s.name for s in workflow.steps if s.step_id == step_id)
                log_workflow_step(logger, workflow.plan_id, step_id, result.status, name=step_name)
                console.print(f"[{color}]{status_icon} {step_name}[/]")
    
    async def _consolidate_results(self, workflow: WorkflowPlan) -> str:
        """Consolidate all step results into a final summary"""
        logger.info(f"Consolidating results for workflow {workflow.plan_id}")
        successful_steps = [s for s in workflow.steps if s.status == "completed"]
        
        if not successful_steps:
            logger.warning(f"No successful steps to consolidate for workflow {workflow.plan_id}")
            return "No steps completed successfully."
        
        results_text = "\n\n".join(
            f"## {s.name}\n{s.result.response}" 
            for s in successful_steps
        )
        
        consolidation_response = await self.client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"""Consolidate these workflow results into a coherent final deliverable.

GOAL: {workflow.goal}

STEP RESULTS:
{results_text}

Create a comprehensive summary that:
1. Synthesizes all the work done
2. Presents the final deliverable
3. Notes any issues or incomplete items
4. Suggests next steps if applicable""",
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=2048)
            )
        )
        
        return consolidation_response.text
    
    async def research_then_code(
        self,
        research_query: str,
        coding_task: str,
        context: Optional[str] = None
    ) -> dict[str, ForkResult]:
        """
        Two-phase workflow: Research first, then code with research context.
        
        Common pattern for implementing features based on best practices.
        """
        workflow_id = self._generate_workflow_id()
        
        console.print(Panel(
            f"[bold blue]Research:[/bold blue] {research_query}\n"
            f"[bold green]Then Code:[/bold green] {coding_task}",
            title=f"📚→💻 Research Then Code: {workflow_id}"
        ))
        
        # Phase 1: Research
        console.print("[cyan]Phase 1: Research...[/cyan]")
        research_result = self.forker.fork(ForkConfig(
            task=research_query,
            agent_type=AgentType.RESEARCH,
            enable_search=True,
            context_summary=context
        ))
        
        if research_result.status != "success":
            return {"research": research_result, "code": None}
        
        console.print("[green]✓ Research complete[/green]")
        
        # Phase 2: Code with research context
        console.print("[cyan]Phase 2: Implementation...[/cyan]")
        
        code_context = f"""
Research findings:
{research_result.response}

{f"Additional context: {context}" if context else ""}
"""
        
        code_result = self.forker.fork(ForkConfig(
            task=coding_task,
            agent_type=AgentType.CODE,
            context_summary=code_context
        ))
        
        if code_result.status == "success":
            console.print("[green]✓ Implementation complete[/green]")
        else:
            console.print("[red]✗ Implementation failed[/red]")
        
        return {
            "research": research_result,
            "code": code_result
        }
    
    async def map_reduce(
        self,
        items: list[str],
        map_task_template: str,
        reduce_task: str,
        agent_type: AgentType = AgentType.ANALYSIS,
        max_concurrent: int = 5
    ) -> dict[str, Any]:
        """
        Map-reduce pattern for batch processing.
        
        1. Map: Process each item with the template
        2. Reduce: Consolidate all results
        """
        workflow_id = self._generate_workflow_id()
        
        console.print(Panel(
            f"[bold]Items:[/bold] {len(items)}\n"
            f"[bold]Map:[/bold] {map_task_template[:50]}...\n"
            f"[bold]Reduce:[/bold] {reduce_task[:50]}...",
            title=f"🗺️ Map-Reduce: {workflow_id}"
        ))
        
        # Map phase
        console.print(f"[cyan]Map phase: Processing {len(items)} items...[/cyan]")
        
        map_tasks = [
            map_task_template.format(item=item)
            for item in items
        ]
        
        swarm_result = await self.forker.swarm_execute(
            tasks=map_tasks,
            agent_type=agent_type,
            max_concurrent=max_concurrent,
            consolidate=False  # We'll do custom reduce
        )
        
        console.print(f"[green]✓ Map complete: {swarm_result.completed}/{swarm_result.total_tasks}[/green]")
        
        # Reduce phase
        console.print("[cyan]Reduce phase: Consolidating results...[/cyan]")
        
        successful_results = [
            r.response for r in swarm_result.results if r.status == "success"
        ]
        
        reduce_input = "\n\n---\n\n".join(successful_results)
        
        reduce_result = self.forker.fork(ForkConfig(
            task=f"{reduce_task}\n\nInputs to reduce:\n{reduce_input}",
            agent_type=AgentType.ANALYSIS,
            thinking_budget=4096
        ))
        
        console.print("[green]✓ Reduce complete[/green]")
        
        return {
            "map_results": swarm_result,
            "reduce_result": reduce_result,
            "items_processed": len(items),
            "items_successful": swarm_result.completed
        }
    
    async def iterative_refinement(
        self,
        initial_task: str,
        refinement_criteria: str,
        max_iterations: int = 3,
        agent_type: AgentType = AgentType.GENERAL
    ) -> list[ForkResult]:
        """
        Iteratively refine output based on criteria.
        
        Each iteration reviews and improves the previous output.
        """
        workflow_id = self._generate_workflow_id()
        
        console.print(Panel(
            f"[bold]Task:[/bold] {initial_task}\n"
            f"[bold]Criteria:[/bold] {refinement_criteria}\n"
            f"[bold]Max iterations:[/bold] {max_iterations}",
            title=f"🔄 Iterative Refinement: {workflow_id}"
        ))
        
        results = []
        current_output = None
        
        for i in range(max_iterations):
            console.print(f"[cyan]Iteration {i + 1}/{max_iterations}...[/cyan]")
            
            if current_output is None:
                # First iteration
                task = initial_task
            else:
                # Refinement iteration
                task = f"""Review and improve this output based on the criteria.

PREVIOUS OUTPUT:
{current_output}

REFINEMENT CRITERIA:
{refinement_criteria}

Either improve the output or state "SATISFACTORY" if it meets all criteria."""
            
            result = self.forker.fork(ForkConfig(
                task=task,
                agent_type=agent_type
            ))
            
            results.append(result)
            
            if result.status == "success":
                current_output = result.response
                
                if "SATISFACTORY" in result.response.upper():
                    console.print(f"[green]✓ Converged after {i + 1} iterations[/green]")
                    break
            else:
                console.print(f"[red]✗ Iteration {i + 1} failed[/red]")
                break
        
        return results


async def main():
    """CLI interface for orchestrator"""
    parser = argparse.ArgumentParser(description="Agent Orchestrator")
    subparsers = parser.add_subparsers(dest="command", help="Workflow type")
    
    # Plan and execute
    pe_parser = subparsers.add_parser("plan-and-execute", help="Plan steps then execute")
    pe_parser.add_argument("--goal", "-g", required=True, help="Goal to achieve")
    pe_parser.add_argument("--context", "-c", help="Additional context")
    pe_parser.add_argument("--max-steps", type=int, default=10, help="Maximum steps")
    
    # Research then code
    rtc_parser = subparsers.add_parser("research-then-code", help="Research first, then implement")
    rtc_parser.add_argument("--research", "-r", required=True, help="Research query")
    rtc_parser.add_argument("--task", "-t", required=True, help="Coding task")
    rtc_parser.add_argument("--context", "-c", help="Additional context")
    
    # Map reduce
    mr_parser = subparsers.add_parser("map-reduce", help="Process items in parallel then reduce")
    mr_parser.add_argument("--items", "-i", nargs="+", required=True, help="Items to process")
    mr_parser.add_argument("--map-template", "-m", required=True, help="Map task template (use {item})")
    mr_parser.add_argument("--reduce", "-r", required=True, help="Reduce task")
    
    # Iterative refinement
    ir_parser = subparsers.add_parser("iterative", help="Iteratively refine output")
    ir_parser.add_argument("--task", "-t", required=True, help="Initial task")
    ir_parser.add_argument("--criteria", "-c", required=True, help="Refinement criteria")
    ir_parser.add_argument("--max-iterations", type=int, default=3, help="Max iterations")
    
    args = parser.parse_args()
    
    orchestrator = AgentOrchestrator()
    
    if args.command == "plan-and-execute":
        result = await orchestrator.plan_and_execute(
            goal=args.goal,
            context=args.context,
            max_steps=args.max_steps
        )
        console.print(Panel(
            Markdown(result.final_result or "No final result"),
            title=f"📋 Final Result: {result.plan_id}"
        ))
        
    elif args.command == "research-then-code":
        results = await orchestrator.research_then_code(
            research_query=args.research,
            coding_task=args.task,
            context=args.context
        )
        if results["code"]:
            console.print(Panel(
                Markdown(results["code"].response),
                title="💻 Implementation"
            ))
        
    elif args.command == "map-reduce":
        results = await orchestrator.map_reduce(
            items=args.items,
            map_task_template=args.map_template,
            reduce_task=args.reduce
        )
        console.print(Panel(
            Markdown(results["reduce_result"].response),
            title="📊 Reduced Result"
        ))
        
    elif args.command == "iterative":
        results = await orchestrator.iterative_refinement(
            initial_task=args.task,
            refinement_criteria=args.criteria,
            max_iterations=args.max_iterations
        )
        final = results[-1]
        console.print(Panel(
            Markdown(final.response),
            title=f"🔄 Final (after {len(results)} iterations)"
        ))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())