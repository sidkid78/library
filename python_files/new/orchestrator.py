"""
Gemini Multi-Agent Orchestrator with R-F-D Pattern
===================================================

Based on the agentic engineering briefing principles:
- Retain: Orchestrator maintains high-level context
- Focus: Workers get minimal, task-specific context  
- Delete: Workers are ephemeral - context doesn't persist

Key Features:
- Structured task decomposition with Pydantic schemas
- Parallel worker execution with asyncio
- Progressive context disclosure
- Full agent lifecycle management (CRUD)
- Built-in observability and cost tracking
"""

from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import Literal, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import uuid
import time
import json


# =============================================================================
# SCHEMAS - Structured outputs for reliable orchestration
# =============================================================================

class TaskPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SubTask(BaseModel):
    """A focused task for a worker agent."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    role: str = Field(description="The specialized role this worker should assume")
    objective: str = Field(description="Clear, specific objective for this worker")
    required_context: list[str] = Field(
        default_factory=list,
        description="Specific context items needed (minimal - progressive disclosure)"
    )
    expected_output: str = Field(description="What format/content the output should have")
    dependencies: list[str] = Field(
        default_factory=list,
        description="IDs of tasks that must complete first"
    )
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)


class TaskPlan(BaseModel):
    """Orchestrator's decomposition of a complex request."""
    analysis: str = Field(description="Brief analysis of what the request requires")
    tasks: list[SubTask] = Field(description="Decomposed sub-tasks for workers")
    execution_strategy: Literal["parallel", "sequential", "hybrid"] = Field(
        description="How tasks should be executed"
    )
    synthesis_approach: str = Field(
        description="How to combine worker outputs into final response"
    )


class WorkerResult(BaseModel):
    """Structured output from a worker agent."""
    task_id: str
    status: Literal["success", "partial", "failed"]
    output: str
    confidence: float = Field(ge=0.0, le=1.0)
    artifacts: list[str] = Field(default_factory=list, description="Any generated files/code")
    notes: str = Field(default="", description="Additional observations")


class SynthesizedResponse(BaseModel):
    """Final response after synthesizing all worker outputs."""
    summary: str = Field(description="Executive summary of the work done")
    detailed_response: str = Field(description="Full synthesized response")
    key_findings: list[str] = Field(default_factory=list)
    artifacts: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    worker_contributions: dict[str, str] = Field(
        default_factory=dict,
        description="Summary of what each worker contributed"
    )


# =============================================================================
# OBSERVABILITY - Track agent performance and costs
# =============================================================================

@dataclass
class AgentMetrics:
    """Metrics for a single agent execution."""
    agent_id: str
    agent_role: str
    start_time: datetime
    end_time: Optional[datetime] = None
    input_tokens: int = 0
    output_tokens: int = 0
    thinking_tokens: int = 0
    tool_calls: int = 0
    status: str = "running"
    error: Optional[str] = None
    
    @property
    def duration_ms(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return 0
    
    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens + self.thinking_tokens
    
    @property
    def estimated_cost(self) -> float:
        """Rough cost estimate based on Gemini 2.5 Flash pricing."""
        # Approximate: $0.075/1M input, $0.30/1M output for Flash
        input_cost = (self.input_tokens / 1_000_000) * 0.075
        output_cost = (self.output_tokens / 1_000_000) * 0.30
        thinking_cost = (self.thinking_tokens / 1_000_000) * 0.30
        return input_cost + output_cost + thinking_cost


@dataclass 
class OrchestratorMetrics:
    """Aggregate metrics for an orchestration run."""
    run_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    agent_metrics: list[AgentMetrics] = field(default_factory=list)
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    
    @property
    def total_tokens(self) -> int:
        return sum(m.total_tokens for m in self.agent_metrics)
    
    @property
    def total_cost(self) -> float:
        return sum(m.estimated_cost for m in self.agent_metrics)
    
    @property
    def duration_ms(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return 0
    
    def summary(self) -> dict:
        return {
            "run_id": self.run_id,
            "duration_ms": self.duration_ms,
            "total_tokens": self.total_tokens,
            "estimated_cost_usd": round(self.total_cost, 6),
            "tasks": {
                "total": self.total_tasks,
                "completed": self.completed_tasks,
                "failed": self.failed_tasks
            },
            "agents_spawned": len(self.agent_metrics)
        }


# =============================================================================
# AGENT REGISTRY - CRUD for managing agent lifecycle
# =============================================================================

@dataclass
class AgentInstance:
    """Represents a spawned agent instance."""
    id: str
    role: str
    status: Literal["idle", "running", "completed", "failed", "deleted"]
    created_at: datetime
    task: Optional[SubTask] = None
    result: Optional[WorkerResult] = None
    metrics: Optional[AgentMetrics] = None


class AgentRegistry:
    """
    Manages agent lifecycle - the CRUD layer for agents.
    
    Key principle: Agents are ephemeral resources. 
    Create them, let them focus, then DELETE them.
    """
    
    def __init__(self):
        self._agents: dict[str, AgentInstance] = {}
        self._deleted_count: int = 0
    
    def create(self, role: str, task: Optional[SubTask] = None) -> AgentInstance:
        """Spawn a new agent instance."""
        agent_id = f"agent_{str(uuid.uuid4())[:8]}"
        agent = AgentInstance(
            id=agent_id,
            role=role,
            status="idle",
            created_at=datetime.now(),
            task=task
        )
        self._agents[agent_id] = agent
        return agent
    
    def read(self, agent_id: str) -> Optional[AgentInstance]:
        """Get agent by ID."""
        return self._agents.get(agent_id)
    
    def list_active(self) -> list[AgentInstance]:
        """List all non-deleted agents."""
        return [a for a in self._agents.values() if a.status != "deleted"]
    
    def update(self, agent_id: str, **kwargs) -> Optional[AgentInstance]:
        """Update agent properties."""
        if agent := self._agents.get(agent_id):
            for key, value in kwargs.items():
                if hasattr(agent, key):
                    setattr(agent, key, value)
            return agent
        return None
    
    def delete(self, agent_id: str) -> bool:
        """
        Mark agent as deleted - releases context.
        
        This is the KEY to R-F-D: once a worker completes,
        DELETE it so its context doesn't pollute the system.
        """
        if agent := self._agents.get(agent_id):
            agent.status = "deleted"
            self._deleted_count += 1
            # In a real system, you might archive metrics before full deletion
            return True
        return False
    
    def cleanup_completed(self) -> int:
        """Delete all completed agents - bulk context cleanup."""
        deleted = 0
        for agent_id, agent in list(self._agents.items()):
            if agent.status == "completed":
                self.delete(agent_id)
                deleted += 1
        return deleted
    
    @property
    def stats(self) -> dict:
        """Get registry statistics."""
        statuses = {}
        for agent in self._agents.values():
            statuses[agent.status] = statuses.get(agent.status, 0) + 1
        return {
            "total_created": len(self._agents),
            "total_deleted": self._deleted_count,
            "by_status": statuses
        }


# =============================================================================
# TOOL REGISTRY - Progressive disclosure of capabilities
# =============================================================================

class ToolRegistry:
    """
    Manages tools with progressive disclosure.
    
    Instead of loading ALL tools upfront (expensive!), 
    agents query the index and load specific tools on-demand.
    """
    
    def __init__(self):
        self._tools: dict[str, Callable] = {}
        self._tool_docs: dict[str, str] = {}
    
    def register(self, name: str, func: Callable, doc: str = ""):
        """Register a tool with optional documentation."""
        self._tools[name] = func
        self._tool_docs[name] = doc or func.__doc__ or "No documentation"
    
    def get_index(self) -> str:
        """
        Get minimal tool index - just names and one-line descriptions.
        This is what agents see FIRST (low context cost).
        """
        lines = ["Available tools:"]
        for name, doc in self._tool_docs.items():
            # Just first line of doc
            first_line = doc.split('\n')[0].strip()
            lines.append(f"  - {name}: {first_line}")
        return '\n'.join(lines)
    
    def get_tool_doc(self, name: str) -> str:
        """Get full documentation for a specific tool (on-demand)."""
        return self._tool_docs.get(name, f"Tool '{name}' not found")
    
    def get_tool(self, name: str) -> Optional[Callable]:
        """Get the actual tool function."""
        return self._tools.get(name)
    
    def get_tools_for_task(self, tool_names: list[str]) -> list[Callable]:
        """Get specific tools needed for a task."""
        return [self._tools[name] for name in tool_names if name in self._tools]


# =============================================================================
# THE ORCHESTRATOR - The brain that coordinates everything
# =============================================================================

class GeminiOrchestrator:
    """
    Multi-Agent Orchestrator implementing R-F-D pattern.
    
    Architecture:
    1. RETAIN: Orchestrator keeps high-level context and plan
    2. FOCUS: Workers get minimal, task-specific context
    3. DELETE: Workers are destroyed after completing their task
    
    This prevents context pollution and enables massive parallelization.
    """
    
    def __init__(
        self,
        orchestrator_model: str = "gemini-2.5-pro",
        worker_model: str = "gemini-2.5-flash",
        thinking_budget_orchestrator: int = 2048,
        thinking_budget_worker: int = 0,  # Workers are fast, no thinking
    ):
        self.client = genai.Client()
        self.orchestrator_model = orchestrator_model
        self.worker_model = worker_model
        self.thinking_budget_orchestrator = thinking_budget_orchestrator
        self.thinking_budget_worker = thinking_budget_worker
        
        self.registry = AgentRegistry()
        self.tool_registry = ToolRegistry()
        self.current_metrics: Optional[OrchestratorMetrics] = None
        
        # Register built-in meta-tools
        self._register_meta_tools()
    
    def _register_meta_tools(self):
        """Register tools that help with orchestration itself."""
        
        def list_available_tools() -> str:
            """Get the index of all available tools."""
            return self.tool_registry.get_index()
        
        def get_tool_documentation(tool_name: str) -> str:
            """Get detailed documentation for a specific tool.
            
            Args:
                tool_name: Name of the tool to get docs for
            """
            return self.tool_registry.get_tool_doc(tool_name)
        
        self.tool_registry.register("list_tools", list_available_tools)
        self.tool_registry.register("get_tool_docs", get_tool_documentation)
    
    def register_tool(self, name: str, func: Callable, doc: str = ""):
        """Register a tool that workers can use."""
        self.tool_registry.register(name, func, doc)
    
    async def _plan_tasks(self, request: str, context: str = "") -> TaskPlan:
        """
        Phase 1: Orchestrator decomposes the request into focused sub-tasks.
        
        Uses thinking for better decomposition.
        """
        system_prompt = """You are an orchestrator agent responsible for decomposing complex requests 
into focused, manageable sub-tasks for worker agents.

PRINCIPLES:
1. Each sub-task should have ONE clear objective
2. Workers should be able to complete their task independently
3. Minimize context needed for each worker (progressive disclosure)
4. Identify true dependencies vs. tasks that can run in parallel

Available tools for workers:
{tools}

Decompose the user's request into sub-tasks. Be specific about:
- What role/expertise each worker needs
- Exactly what they should produce
- What minimal context they need
- Which tasks depend on others
""".format(tools=self.tool_registry.get_index())

        response = await self.client.aio.models.generate_content(
            model=self.orchestrator_model,
            contents=f"Context: {context}\n\nRequest: {request}" if context else request,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=TaskPlan,
                thinking_config=types.ThinkingConfig(
                    thinking_budget=self.thinking_budget_orchestrator
                )
            )
        )
        
        # Track metrics
        if self.current_metrics and response.usage_metadata:
            orchestrator_metrics = AgentMetrics(
                agent_id="orchestrator",
                agent_role="task_decomposition",
                start_time=datetime.now(),
                end_time=datetime.now(),
                input_tokens=response.usage_metadata.prompt_token_count or 0,
                output_tokens=response.usage_metadata.candidates_token_count or 0,
                thinking_tokens=getattr(response.usage_metadata, 'thoughts_token_count', 0) or 0,
                status="completed"
            )
            self.current_metrics.agent_metrics.append(orchestrator_metrics)
        
        return TaskPlan.model_validate_json(response.text)
    
    async def _execute_worker(
        self, 
        task: SubTask, 
        tools: list[Callable],
        shared_context: str = ""
    ) -> WorkerResult:
        """
        Execute a single worker agent on a focused task.
        
        Key: Worker gets MINIMAL context - just what it needs.
        After completion, worker is DELETED (context doesn't persist).
        """
        # Create agent in registry
        agent = self.registry.create(role=task.role, task=task)
        self.registry.update(agent.id, status="running")
        
        start_time = datetime.now()
        metrics = AgentMetrics(
            agent_id=agent.id,
            agent_role=task.role,
            start_time=start_time
        )
        
        # Focused system prompt - minimal context
        system_prompt = f"""You are a focused worker agent with role: {task.role}

YOUR SINGLE OBJECTIVE: {task.objective}

EXPECTED OUTPUT FORMAT: {task.expected_output}

CONSTRAINTS:
- Stay focused on your specific task
- Do not try to solve the entire problem
- Report your findings clearly
- Note any blockers or uncertainties

{f"CONTEXT: {shared_context}" if shared_context else ""}
"""
        
        try:
            response = await self.client.aio.models.generate_content(
                model=self.worker_model,
                contents=task.objective,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    tools=tools if tools else None,
                    response_mime_type="application/json",
                    response_schema=WorkerResult,
                    thinking_config=types.ThinkingConfig(
                        thinking_budget=self.thinking_budget_worker
                    )
                )
            )
            
            # Parse result
            result_data = json.loads(response.text)
            result_data["task_id"] = task.id
            result = WorkerResult.model_validate(result_data)
            
            # Update metrics
            metrics.end_time = datetime.now()
            metrics.status = "completed"
            if response.usage_metadata:
                metrics.input_tokens = response.usage_metadata.prompt_token_count or 0
                metrics.output_tokens = response.usage_metadata.candidates_token_count or 0
                metrics.thinking_tokens = getattr(response.usage_metadata, 'thoughts_token_count', 0) or 0
            
            # Update agent
            self.registry.update(agent.id, status="completed", result=result, metrics=metrics)
            
        except Exception as e:
            metrics.end_time = datetime.now()
            metrics.status = "failed"
            metrics.error = str(e)
            
            result = WorkerResult(
                task_id=task.id,
                status="failed",
                output=f"Worker failed: {str(e)}",
                confidence=0.0
            )
            self.registry.update(agent.id, status="failed", result=result, metrics=metrics)
        
        # Track metrics
        if self.current_metrics:
            self.current_metrics.agent_metrics.append(metrics)
        
        # DELETE the worker - this is the key to R-F-D!
        # The worker's context is gone, but its result is preserved
        self.registry.delete(agent.id)
        
        return result
    
    async def _execute_tasks(
        self, 
        plan: TaskPlan, 
        tools: list[Callable],
        shared_context: str = ""
    ) -> list[WorkerResult]:
        """
        Execute all tasks according to the plan's strategy.
        """
        results: list[WorkerResult] = []
        completed_ids: set[str] = set()
        
        if plan.execution_strategy == "parallel":
            # All tasks run simultaneously
            tasks_coros = [
                self._execute_worker(task, tools, shared_context) 
                for task in plan.tasks
            ]
            results = await asyncio.gather(*tasks_coros)
            
        elif plan.execution_strategy == "sequential":
            # Tasks run one after another
            for task in plan.tasks:
                result = await self._execute_worker(task, tools, shared_context)
                results.append(result)
                completed_ids.add(task.id)
                
        else:  # hybrid - respect dependencies
            pending = {task.id: task for task in plan.tasks}
            
            while pending:
                # Find tasks whose dependencies are met
                ready = [
                    task for task_id, task in pending.items()
                    if all(dep in completed_ids for dep in task.dependencies)
                ]
                
                if not ready:
                    # Deadlock or circular dependency
                    break
                
                # Execute ready tasks in parallel
                batch_coros = [
                    self._execute_worker(task, tools, shared_context)
                    for task in ready
                ]
                batch_results = await asyncio.gather(*batch_coros)
                
                for task, result in zip(ready, batch_results):
                    results.append(result)
                    completed_ids.add(task.id)
                    del pending[task.id]
        
        return results
    
    async def _synthesize_results(
        self, 
        original_request: str,
        plan: TaskPlan, 
        results: list[WorkerResult]
    ) -> SynthesizedResponse:
        """
        Phase 3: Orchestrator synthesizes all worker outputs into final response.
        """
        # Build synthesis context
        worker_outputs = "\n\n".join([
            f"=== Worker: {plan.tasks[i].role} ===\n"
            f"Task: {plan.tasks[i].objective}\n"
            f"Status: {result.status}\n"
            f"Output: {result.output}\n"
            f"Confidence: {result.confidence}"
            for i, result in enumerate(results)
        ])
        
        system_prompt = f"""You are synthesizing the outputs from multiple worker agents 
into a coherent final response.

SYNTHESIS APPROACH: {plan.synthesis_approach}

Original request: {original_request}

Combine the worker outputs into a comprehensive response that:
1. Directly addresses the original request
2. Integrates insights from all workers
3. Notes any conflicts or uncertainties
4. Provides actionable conclusions
"""
        
        response = await self.client.aio.models.generate_content(
            model=self.orchestrator_model,
            contents=f"Worker outputs to synthesize:\n\n{worker_outputs}",
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=SynthesizedResponse,
                thinking_config=types.ThinkingConfig(
                    thinking_budget=self.thinking_budget_orchestrator
                )
            )
        )
        
        # Track metrics
        if self.current_metrics and response.usage_metadata:
            synthesis_metrics = AgentMetrics(
                agent_id="orchestrator",
                agent_role="synthesis",
                start_time=datetime.now(),
                end_time=datetime.now(),
                input_tokens=response.usage_metadata.prompt_token_count or 0,
                output_tokens=response.usage_metadata.candidates_token_count or 0,
                thinking_tokens=getattr(response.usage_metadata, 'thoughts_token_count', 0) or 0,
                status="completed"
            )
            self.current_metrics.agent_metrics.append(synthesis_metrics)
        
        return SynthesizedResponse.model_validate_json(response.text)
    
    async def run(
        self, 
        request: str, 
        context: str = "",
        tools: Optional[list[Callable]] = None
    ) -> tuple[SynthesizedResponse, OrchestratorMetrics]:
        """
        Execute the full orchestration pipeline.
        
        Pipeline:
        1. Plan: Decompose request into focused sub-tasks
        2. Execute: Run workers (parallel/sequential/hybrid)
        3. Synthesize: Combine outputs into final response
        4. Cleanup: Delete all workers (R-F-D complete)
        
        Returns:
            Tuple of (final response, metrics for observability)
        """
        # Initialize metrics
        run_id = str(uuid.uuid4())[:8]
        self.current_metrics = OrchestratorMetrics(
            run_id=run_id,
            start_time=datetime.now()
        )
        
        # Collect tools
        all_tools = tools or []
        # Add meta-tools for tool discovery
        all_tools.extend([
            self.tool_registry.get_tool("list_tools"),
            self.tool_registry.get_tool("get_tool_docs")
        ])
        all_tools = [t for t in all_tools if t is not None]
        
        # Phase 1: Plan
        print(f"[{run_id}] 📋 Planning task decomposition...")
        plan = await self._plan_tasks(request, context)
        self.current_metrics.total_tasks = len(plan.tasks)
        print(f"[{run_id}] Created {len(plan.tasks)} sub-tasks ({plan.execution_strategy})")
        
        # Phase 2: Execute
        print(f"[{run_id}] 🔧 Executing workers...")
        results = await self._execute_tasks(plan, all_tools, context)
        
        # Count outcomes
        for result in results:
            if result.status == "success":
                self.current_metrics.completed_tasks += 1
            else:
                self.current_metrics.failed_tasks += 1
        
        print(f"[{run_id}] Workers complete: {self.current_metrics.completed_tasks} success, {self.current_metrics.failed_tasks} failed")
        
        # Phase 3: Synthesize
        print(f"[{run_id}] 🧠 Synthesizing results...")
        final_response = await self._synthesize_results(request, plan, results)
        
        # Finalize metrics
        self.current_metrics.end_time = datetime.now()
        
        # Cleanup - delete any remaining agents
        cleaned = self.registry.cleanup_completed()
        print(f"[{run_id}] 🧹 Cleaned up {cleaned} agents")
        
        # Summary
        summary = self.current_metrics.summary()
        print(f"[{run_id}] ✅ Complete | {summary['duration_ms']:.0f}ms | {summary['total_tokens']} tokens | ${summary['estimated_cost_usd']:.4f}")
        
        return final_response, self.current_metrics


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_orchestrator(**kwargs) -> GeminiOrchestrator:
    """Factory function to create an orchestrator with common configurations."""
    return GeminiOrchestrator(**kwargs)


async def quick_orchestrate(request: str, tools: list[Callable] = None) -> str:
    """Quick way to orchestrate a request and get just the text response."""
    orchestrator = create_orchestrator()
    response, _ = await orchestrator.run(request, tools=tools)
    return response.detailed_response