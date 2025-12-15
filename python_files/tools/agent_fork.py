# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "google-genai>=1.0.0",
#     "pydantic>=2.0.0",
#     "rich>=13.0.0",
# ]
# ///
"""
Gemini Agent Fork Tool

Fork conversation context to new Gemini agents for parallel execution,
specialized task routing, and multi-agent orchestration.

Now with TOOL EXECUTION support - forked agents can actually create files!

Usage:
    uv run agent_fork.py --task "Your task" --type code
    uv run agent_fork.py --task "Research X" --type research --search
    uv run agent_fork.py --swarm --tasks "task1" "task2" "task3"
"""

from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import Optional, Literal, Any
from enum import Enum
import asyncio
import argparse
import json
import os
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

# Logging setup
from .logging_config import get_logger, log_api_call, log_api_response, log_error, log_tool_execution, ensure_logging_setup
logger = get_logger('agent_fork')

# Tool integration
try:
    from .agent_tools_integration import AgentToolsManager
except ImportError:
    AgentToolsManager = None

console = Console()


class AgentType(str, Enum):
    """Types of specialized agents available"""
    CODE = "code"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    CREATIVE = "creative"
    GENERAL = "general"


class ForkConfig(BaseModel):
    """Configuration for forking context to a new agent"""
    task: str = Field(description="The task for the forked agent")
    agent_type: AgentType = Field(default=AgentType.GENERAL)
    context_summary: Optional[str] = Field(default=None, description="Summary of previous context")
    model: Optional[str] = Field(default=None, description="Override default model")
    thinking_budget: Optional[int] = Field(default=None, description="Override thinking budget")
    enable_search: bool = Field(default=False, description="Enable Google Search grounding")
    enable_code_execution: bool = Field(default=False, description="Enable code execution")
    enable_tools: bool = Field(default=True, description="Enable file system tools")
    system_instruction: Optional[str] = Field(default=None, description="Custom system instruction")
    max_tool_turns: int = Field(default=10, description="Max turns for tool execution loop")


class ForkResult(BaseModel):
    """Result from a forked agent execution"""
    fork_id: str
    agent_type: AgentType
    task: str
    status: Literal["success", "error", "partial"]
    response: str
    model_used: str
    thinking_tokens: Optional[int] = None
    cached_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    tools_executed: list[str] = Field(default_factory=list)
    files_created: list[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    error: Optional[str] = None


class SwarmResult(BaseModel):
    """Result from parallel swarm execution"""
    swarm_id: str
    total_tasks: int
    completed: int
    failed: int
    results: list[ForkResult]
    consolidated_summary: Optional[str] = None


# Agent configurations by type
AGENT_CONFIGS = {
    AgentType.CODE: {
        "model": "gemini-2.5-pro",
        "thinking_budget": 8192,
        "system_instruction": """You are an expert software engineer with access to file system tools.

CRITICAL: You MUST use the provided tools to create files. Do NOT just describe what files to create.

Your approach:
1. Analyze the requirements
2. Plan your implementation
3. USE THE TOOLS to create each file (create_file, create_directory, etc.)
4. Verify your work

When creating files, use COMPLETE, WORKING code - no placeholders or TODOs."""
    },
    AgentType.RESEARCH: {
        "model": "gemini-2.5-flash",
        "thinking_budget": 2048,
        "enable_search": True,
        "system_instruction": """You are an expert researcher with access to current information.

Your strengths:
- Finding accurate, up-to-date information
- Synthesizing multiple sources
- Providing well-cited answers

Use Google Search to find current information."""
    },
    AgentType.ANALYSIS: {
        "model": "gemini-2.5-pro",
        "thinking_budget": 4096,
        "system_instruction": """You are an expert analyst with access to file tools.

Use tools to read files and create analysis reports."""
    },
    AgentType.CREATIVE: {
        "model": "gemini-2.5-flash",
        "thinking_budget": 1024,
        "system_instruction": """You are a creative assistant skilled in ideation."""
    },
    AgentType.GENERAL: {
        "model": "gemini-2.5-flash",
        "thinking_budget": 1024,
        "system_instruction": """You are a helpful AI assistant with access to file system tools.

Use the tools when needed to accomplish your tasks."""
    }
}


class AgentForker:
    """
    Fork conversation context to new Gemini agents with TOOL EXECUTION.
    
    Now supports actual file creation via AgentToolsManager!
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        tools_manager: Optional[Any] = None,
        workspace_root: Optional[str] = None
    ):
        """Initialize the forker with GenAI client and optional tools"""
        ensure_logging_setup()
        logger.info("Initializing AgentForker")
        
        key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        
        if not key:
            logger.error("No API key found - GEMINI_API_KEY not set")
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        self.client = genai.Client(api_key=key)
        self._fork_counter = 0
        
        # Initialize tools manager
        if tools_manager:
            self.tools_manager = tools_manager
        elif workspace_root and AgentToolsManager:
            self.tools_manager = AgentToolsManager(workspace_root=workspace_root)
            logger.info(f"AgentToolsManager initialized for {workspace_root}")
        else:
            self.tools_manager = None
            logger.warning("No tools manager - forked agents cannot execute file operations")
        
        logger.info("AgentForker initialized successfully")
    
    def _generate_fork_id(self) -> str:
        """Generate a unique fork ID"""
        self._fork_counter += 1
        timestamp = datetime.now().strftime("%H%M%S")
        return f"fork_{timestamp}_{self._fork_counter:03d}"
    
    def _build_config(self, fork_config: ForkConfig) -> tuple[str, types.GenerateContentConfig]:
        """Build the generation config based on fork configuration"""
        agent_config = AGENT_CONFIGS.get(fork_config.agent_type, AGENT_CONFIGS[AgentType.GENERAL])
        
        model = fork_config.model or agent_config.get("model", "gemini-2.5-flash")
        thinking_budget = fork_config.thinking_budget or agent_config.get("thinking_budget", 1024)
        
        # Build system instruction
        base_instruction = fork_config.system_instruction or agent_config.get("system_instruction", "")
        
        if fork_config.context_summary:
            system_instruction = f"""{base_instruction}

## Previous Context Summary
{fork_config.context_summary}

Use this context to inform your response."""
        else:
            system_instruction = base_instruction
        
        # Build tools list
        tools = []
        
        # Add file system tools if enabled and available
        if fork_config.enable_tools and self.tools_manager:
            tools.extend(self.tools_manager.get_tool_declarations())
            logger.debug(f"Added {len(tools)} file system tools")
        
        if fork_config.enable_search or agent_config.get("enable_search", False):
            tools.append(types.Tool(google_search=types.GoogleSearch()))
        
        if fork_config.enable_code_execution or agent_config.get("enable_code_execution", False):
            tools.append(types.Tool(code_execution=types.ToolCodeExecution()))
        
        config_dict = {
            "system_instruction": system_instruction,
            "thinking_config": types.ThinkingConfig(thinking_budget=thinking_budget)
        }
        
        if tools:
            config_dict["tools"] = tools
        
        return model, types.GenerateContentConfig(**config_dict)
    
    def _execute_tool_call(self, function_call) -> dict:
        """Execute a single tool call and return the result"""
        if not self.tools_manager:
            return {"error": "No tools manager available"}
        
        tool_name = function_call.name
        args = dict(function_call.args) if function_call.args else {}
        
        logger.info(f"Executing tool: {tool_name}")
        logger.debug(f"Tool args: {args}")
        
        result = self.tools_manager.execute_tool(tool_name, args)
        
        log_tool_execution(logger, tool_name, args, result)
        
        return result
    
    def fork(self, config: ForkConfig) -> ForkResult:
        """
        Fork context to a new Gemini agent WITH TOOL EXECUTION.
        
        The agent will actually execute file operations using the tools!
        """
        fork_id = self._generate_fork_id()
        logger.info(f"Creating fork {fork_id} - type={config.agent_type.value}")
        
        tools_executed = []
        files_created = []
        all_responses = []
        
        try:
            model, gen_config = self._build_config(config)
            logger.debug(f"Fork {fork_id}: model={model}, tools_enabled={config.enable_tools}")
            
            console.print(Panel(
                f"[bold blue]Forking to {config.agent_type.value} agent[/bold blue]\n"
                f"Model: {model}\n"
                f"Tools: {'enabled' if config.enable_tools and self.tools_manager else 'disabled'}\n"
                f"Task: {config.task[:100]}...",
                title=f"🔀 Fork {fork_id}"
            ))
            
            # Build conversation history for multi-turn
            messages = [types.Content(role="user", parts=[types.Part.from_text(text=config.task)])]
            
            # Tool execution loop
            for turn in range(config.max_tool_turns):
                log_api_call(logger, model, config.task[:100], fork_id=fork_id, turn=turn)
                
                response = self.client.models.generate_content(
                    model=model,
                    contents=messages,
                    config=gen_config
                )
                
                if not response.candidates or not response.candidates[0].content:
                    break
                
                content = response.candidates[0].content
                messages.append(content)
                
                # Check for function calls
                function_calls = []
                text_parts = []
                
                for part in content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        function_calls.append(part.function_call)
                    elif hasattr(part, 'text') and part.text:
                        text_parts.append(part.text)
                
                # Collect text responses
                all_responses.extend(text_parts)
                
                # If no function calls, we're done
                if not function_calls:
                    logger.info(f"Fork {fork_id} completed after {turn+1} turns (no more tool calls)")
                    break
                
                # Execute function calls
                function_responses = []
                for fc in function_calls:
                    tools_executed.append(fc.name)
                    
                    console.print(f"  [yellow]📁 {fc.name}[/yellow]", end="")
                    
                    result = self._execute_tool_call(fc)
                    
                    if result.get("success"):
                        console.print(f" [green]✓[/green]")
                        if fc.name == "create_file":
                            path = dict(fc.args).get("path", "")
                            files_created.append(path)
                    else:
                        console.print(f" [red]✗ {result.get('error', '')[:50]}[/red]")
                    
                    function_responses.append(
                        types.Part.from_function_response(
                            name=fc.name,
                            response={"result": json.dumps(result)}
                        )
                    )
                
                # Add function responses for next turn
                messages.append(types.Content(role="user", parts=function_responses))
            
            # Extract usage metadata from last response
            usage = response.usage_metadata if hasattr(response, 'usage_metadata') else None
            total_tokens = getattr(usage, 'total_token_count', None) if usage else None
            
            log_api_response(logger, model, "success", tokens=total_tokens, fork_id=fork_id)
            logger.info(f"Fork {fork_id} completed - tools={len(tools_executed)}, files={len(files_created)}")
            
            return ForkResult(
                fork_id=fork_id,
                agent_type=config.agent_type,
                task=config.task,
                status="success",
                response="\n\n".join(all_responses),
                model_used=model,
                thinking_tokens=getattr(usage, 'thoughts_token_count', None) if usage else None,
                cached_tokens=getattr(usage, 'cached_content_token_count', None) if usage else None,
                total_tokens=total_tokens,
                tools_executed=tools_executed,
                files_created=files_created
            )
            
        except Exception as e:
            log_error(logger, e, f"fork {fork_id}")
            return ForkResult(
                fork_id=fork_id,
                agent_type=config.agent_type,
                task=config.task,
                status="error",
                response="",
                model_used=config.model or "unknown",
                error=str(e)
            )
    
    async def fork_async(self, config: ForkConfig) -> ForkResult:
        """Async version of fork with tool execution"""
        fork_id = self._generate_fork_id()
        logger.info(f"Creating async fork {fork_id} - type={config.agent_type.value}")
        
        tools_executed = []
        files_created = []
        all_responses = []
        
        try:
            model, gen_config = self._build_config(config)
            
            messages = [types.Content(role="user", parts=[types.Part.from_text(text=config.task)])]
            
            for turn in range(config.max_tool_turns):
                log_api_call(logger, model, config.task[:100], fork_id=fork_id, turn=turn, async_mode=True)
                
                response = await self.client.aio.models.generate_content(
                    model=model,
                    contents=messages,
                    config=gen_config
                )
                
                if not response.candidates or not response.candidates[0].content:
                    break
                
                content = response.candidates[0].content
                messages.append(content)
                
                function_calls = []
                text_parts = []
                
                for part in content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        function_calls.append(part.function_call)
                    elif hasattr(part, 'text') and part.text:
                        text_parts.append(part.text)
                
                all_responses.extend(text_parts)
                
                if not function_calls:
                    logger.info(f"Async fork {fork_id} completed after {turn+1} turns")
                    break
                
                function_responses = []
                for fc in function_calls:
                    tools_executed.append(fc.name)
                    result = self._execute_tool_call(fc)
                    
                    if result.get("success") and fc.name == "create_file":
                        path = dict(fc.args).get("path", "")
                        files_created.append(path)
                    
                    function_responses.append(
                        types.Part.from_function_response(
                            name=fc.name,
                            response={"result": json.dumps(result)}
                        )
                    )
                
                messages.append(types.Content(role="user", parts=function_responses))
            
            usage = response.usage_metadata if hasattr(response, 'usage_metadata') else None
            total_tokens = getattr(usage, 'total_token_count', None) if usage else None
            
            log_api_response(logger, model, "success", tokens=total_tokens, fork_id=fork_id)
            logger.info(f"Async fork {fork_id} completed - tools={len(tools_executed)}, files={len(files_created)}")
            
            return ForkResult(
                fork_id=fork_id,
                agent_type=config.agent_type,
                task=config.task,
                status="success",
                response="\n\n".join(all_responses),
                model_used=model,
                thinking_tokens=getattr(usage, 'thoughts_token_count', None) if usage else None,
                cached_tokens=getattr(usage, 'cached_content_token_count', None) if usage else None,
                total_tokens=total_tokens,
                tools_executed=tools_executed,
                files_created=files_created
            )
            
        except Exception as e:
            log_error(logger, e, f"async fork {fork_id}")
            return ForkResult(
                fork_id=fork_id,
                agent_type=config.agent_type,
                task=config.task,
                status="error",
                response="",
                model_used=config.model or "unknown",
                error=str(e)
            )
    
    async def swarm_execute(
        self,
        tasks: list[str],
        agent_type: AgentType = AgentType.GENERAL,
        context_summary: Optional[str] = None,
        consolidate: bool = True,
        max_concurrent: int = 5
    ) -> SwarmResult:
        """Execute multiple tasks in parallel across an agent swarm"""
        swarm_id = f"swarm_{datetime.now().strftime('%H%M%S')}"
        
        logger.info(f"Starting swarm {swarm_id}: {len(tasks)} tasks, max_concurrent={max_concurrent}")
        
        console.print(Panel(
            f"[bold green]Spawning agent swarm[/bold green]\n"
            f"Tasks: {len(tasks)}\n"
            f"Agent Type: {agent_type.value}",
            title=f"🐝 Swarm {swarm_id}"
        ))
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def limited_fork(task: str) -> ForkResult:
            async with semaphore:
                config = ForkConfig(
                    task=task,
                    agent_type=agent_type,
                    context_summary=context_summary,
                    enable_tools=True
                )
                return await self.fork_async(config)
        
        results = await asyncio.gather(*[limited_fork(task) for task in tasks])
        
        completed = sum(1 for r in results if r.status == "success")
        failed = sum(1 for r in results if r.status == "error")
        
        # Consolidate if requested
        consolidated = None
        if consolidate and completed > 0:
            successful = [r for r in results if r.status == "success"]
            consolidation_prompt = f"""Consolidate these {len(successful)} agent results:

{chr(10).join(f'## {r.fork_id}:{chr(10)}{r.response[:500]}' for r in successful)}

Provide a unified summary."""
            
            consolidation_response = await self.client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=consolidation_prompt,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_budget=1024)
                )
            )
            consolidated = consolidation_response.text
        
        logger.info(f"Swarm {swarm_id} completed: {completed}/{len(tasks)}")
        
        return SwarmResult(
            swarm_id=swarm_id,
            total_tasks=len(tasks),
            completed=completed,
            failed=failed,
            results=list(results),
            consolidated_summary=consolidated
        )


def main():
    """CLI interface for agent forking"""
    parser = argparse.ArgumentParser(description="Fork context to Gemini agents")
    parser.add_argument("--task", "-t", type=str, help="Task for the agent")
    parser.add_argument("--type", "-T", type=str, default="general",
                       choices=["code", "research", "analysis", "creative", "general"])
    parser.add_argument("--context", "-c", type=str, help="Context summary")
    parser.add_argument("--search", "-s", action="store_true", help="Enable Google Search")
    parser.add_argument("--workspace", "-w", type=str, default=".", help="Workspace root")
    parser.add_argument("--no-tools", action="store_true", help="Disable file tools")
    parser.add_argument("--model", "-m", type=str, help="Override model")
    parser.add_argument("--swarm", action="store_true", help="Run in swarm mode")
    parser.add_argument("--tasks", nargs="+", help="Tasks for swarm mode")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    # Initialize forker with workspace
    forker = AgentForker(workspace_root=args.workspace)
    
    if args.swarm and args.tasks:
        result = asyncio.run(forker.swarm_execute(
            tasks=args.tasks,
            agent_type=AgentType(args.type),
            context_summary=args.context
        ))
        
        if args.json:
            print(result.model_dump_json(indent=2))
        else:
            console.print(Panel(
                f"Completed: {result.completed}/{result.total_tasks}\n"
                f"Files created: {sum(len(r.files_created) for r in result.results)}",
                title=f"🐝 Swarm Complete: {result.swarm_id}"
            ))
    
    elif args.task:
        config = ForkConfig(
            task=args.task,
            agent_type=AgentType(args.type),
            context_summary=args.context,
            model=args.model,
            enable_search=args.search,
            enable_tools=not args.no_tools
        )
        
        result = forker.fork(config)
        
        if args.json:
            print(result.model_dump_json(indent=2))
        else:
            if result.status == "success":
                console.print(Panel(
                    f"Tools executed: {len(result.tools_executed)}\n"
                    f"Files created: {len(result.files_created)}\n\n"
                    f"{result.response[:1000]}...",
                    title=f"✅ {result.fork_id} ({result.agent_type.value})"
                ))
            else:
                console.print(f"[red]Error: {result.error}[/red]")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()