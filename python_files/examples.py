# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "google-genai>=1.0.0",
#     "pydantic>=2.0.0",
#     "rich>=13.0.0",
# ]
# ///
"""
Gemini Agent Fork - Demo Examples

Demonstrates all major features of the agent fork system.

Usage:
    uv run examples.py [example_name]
    
Examples:
    uv run examples.py basic_fork
    uv run examples.py code_agent
    uv run examples.py research_agent
    uv run examples.py swarm
    uv run examples.py orchestrator
    uv run examples.py all
"""

import asyncio
import sys
from pathlib import Path

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent / "tools"))

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()


def example_basic_fork():
    """Demonstrate basic agent forking"""
    console.print(Panel("[bold]Example: Basic Agent Fork[/bold]", style="cyan"))
    
    from agent_fork import AgentForker, ForkConfig, AgentType
    
    forker = AgentForker()
    
    # Simple fork
    result = forker.fork(ForkConfig(
        task="Explain the difference between async and threading in Python in 3 sentences.",
        agent_type=AgentType.GENERAL
    ))
    
    console.print(f"[green]Status:[/green] {result.status}")
    console.print(f"[green]Model:[/green] {result.model_used}")
    console.print(Panel(Markdown(result.response), title="Response"))
    
    return result


def example_code_agent():
    """Demonstrate code agent with extended thinking"""
    console.print(Panel("[bold]Example: Code Agent[/bold]", style="green"))
    
    from agent_fork import AgentForker, ForkConfig, AgentType
    
    forker = AgentForker()
    
    result = forker.fork(ForkConfig(
        task="""Write a Python decorator that:
1. Retries a function up to 3 times on exception
2. Uses exponential backoff (1s, 2s, 4s)
3. Logs each retry attempt
4. Preserves the original function's metadata

Include type hints and a docstring.""",
        agent_type=AgentType.CODE,
        thinking_budget=4096
    ))
    
    console.print(f"[green]Status:[/green] {result.status}")
    if result.thinking_tokens:
        console.print(f"[blue]Thinking tokens:[/blue] {result.thinking_tokens}")
    console.print(Panel(Markdown(result.response), title="Code Output"))
    
    return result


def example_research_agent():
    """Demonstrate research agent with Google Search"""
    console.print(Panel("[bold]Example: Research Agent with Google Search[/bold]", style="blue"))
    
    from agent_fork import AgentForker, ForkConfig, AgentType
    
    forker = AgentForker()
    
    result = forker.fork(ForkConfig(
        task="What are the key new features in the Google GenAI Python SDK? Focus on recent additions.",
        agent_type=AgentType.RESEARCH,
        enable_search=True
    ))
    
    console.print(f"[green]Status:[/green] {result.status}")
    console.print(Panel(Markdown(result.response), title="Research Results"))
    
    return result


async def example_swarm():
    """Demonstrate parallel swarm execution"""
    console.print(Panel("[bold]Example: Parallel Agent Swarm[/bold]", style="magenta"))
    
    from agent_fork import AgentForker, AgentType
    
    forker = AgentForker()
    
    # Analyze different aspects in parallel
    tasks = [
        "List 3 advantages of microservices architecture",
        "List 3 challenges of microservices architecture",
        "List 3 best practices for microservices communication",
    ]
    
    result = await forker.swarm_execute(
        tasks=tasks,
        agent_type=AgentType.ANALYSIS,
        max_concurrent=3,
        consolidate=True
    )
    
    console.print(f"[green]Completed:[/green] {result.completed}/{result.total_tasks}")
    
    if result.consolidated_summary:
        console.print(Panel(
            Markdown(result.consolidated_summary),
            title="Consolidated Summary"
        ))
    
    return result


async def example_orchestrator():
    """Demonstrate plan-and-execute workflow"""
    console.print(Panel("[bold]Example: Plan-and-Execute Orchestrator[/bold]", style="yellow"))
    
    from orchestrator import AgentOrchestrator
    
    orchestrator = AgentOrchestrator()
    
    result = await orchestrator.plan_and_execute(
        goal="Design a simple user authentication system for a web API",
        context="Using Python with FastAPI framework",
        max_steps=4  # Keep it small for demo
    )
    
    console.print(f"[green]Workflow Status:[/green] {result.status}")
    console.print(f"[green]Steps:[/green] {len(result.steps)}")
    
    if result.final_result:
        console.print(Panel(
            Markdown(result.final_result[:2000] + "..." if len(result.final_result) > 2000 else result.final_result),
            title="Final Result"
        ))
    
    return result


def example_context_summarizer():
    """Demonstrate context summarization"""
    console.print(Panel("[bold]Example: Context Summarizer[/bold]", style="red"))
    
    from context_summarizer import (
        ContextSummarizer, ConversationHistory, ConversationTurn
    )
    
    summarizer = ContextSummarizer()
    
    # Create sample conversation
    history = ConversationHistory(turns=[
        ConversationTurn(
            role="user",
            content="I want to build a REST API for a todo application"
        ),
        ConversationTurn(
            role="assistant",
            content="Great! I recommend using FastAPI for its performance and automatic OpenAPI docs. We should start by defining the data models. Let's use SQLAlchemy for the ORM and PostgreSQL for the database."
        ),
        ConversationTurn(
            role="user",
            content="Sounds good. What models do we need?"
        ),
        ConversationTurn(
            role="assistant",
            content="We'll need at least two models: User and Todo. The User model should have id, email, and hashed_password. The Todo model needs id, title, description, completed status, and a foreign key to User."
        ),
        ConversationTurn(
            role="user",
            content="Let's implement the models first"
        ),
    ])
    
    summary = summarizer.summarize(history, style="detailed")
    
    console.print(f"[green]Compression:[/green] {summary.compression_ratio:.1f}x")
    console.print(f"[green]Tokens:[/green] ~{summary.token_count}")
    console.print(Panel(Markdown(summary.summary), title="Summary"))
    
    if summary.key_decisions:
        console.print(Panel(
            "\n".join(f"• {d}" for d in summary.key_decisions),
            title="Key Decisions"
        ))
    
    return summary


async def example_research_then_code():
    """Demonstrate research-then-code workflow"""
    console.print(Panel("[bold]Example: Research Then Code[/bold]", style="cyan"))
    
    from orchestrator import AgentOrchestrator
    
    orchestrator = AgentOrchestrator()
    
    results = await orchestrator.research_then_code(
        research_query="What is the recommended way to implement rate limiting in FastAPI?",
        coding_task="Implement a simple rate limiting middleware for FastAPI based on the research",
        context="Building a REST API that needs to handle rate limiting"
    )
    
    console.print("\n[bold]Research Phase:[/bold]")
    if results["research"].status == "success":
        console.print(Panel(
            Markdown(results["research"].response[:1500] + "..."),
            title="Research Findings"
        ))
    
    console.print("\n[bold]Code Phase:[/bold]")
    if results["code"] and results["code"].status == "success":
        console.print(Panel(
            Markdown(results["code"].response[:2000] + "..."),
            title="Implementation"
        ))
    
    return results


async def run_all_examples():
    """Run all examples"""
    console.print(Panel(
        "[bold white on blue] Gemini Agent Fork - All Examples [/bold white on blue]",
        expand=False
    ))
    
    examples = [
        ("Basic Fork", example_basic_fork),
        ("Context Summarizer", example_context_summarizer),
        ("Code Agent", example_code_agent),
        ("Research Agent", example_research_agent),
        ("Parallel Swarm", example_swarm),
        ("Research Then Code", example_research_then_code),
        ("Plan-and-Execute Orchestrator", example_orchestrator),
    ]
    
    for name, example in examples:
        console.print(f"\n{'='*60}")
        console.print(f"[bold] Running: {name} [/bold]")
        console.print(f"{'='*60}\n")
        
        try:
            if asyncio.iscoroutinefunction(example):
                await example()
            else:
                example()
            console.print(f"\n[green]✓ {name} completed[/green]")
        except Exception as e:
            console.print(f"\n[red]✗ {name} failed: {e}[/red]")
        
        # Small delay between examples
        await asyncio.sleep(1)


def main():
    example_map = {
        "basic_fork": example_basic_fork,
        "code_agent": example_code_agent,
        "research_agent": example_research_agent,
        "swarm": example_swarm,
        "orchestrator": example_orchestrator,
        "summarizer": example_context_summarizer,
        "research_then_code": example_research_then_code,
        "all": run_all_examples,
    }
    
    if len(sys.argv) < 2:
        console.print("[bold]Available examples:[/bold]")
        for name in example_map:
            console.print(f"  • {name}")
        console.print("\n[dim]Usage: uv run examples.py <example_name>[/dim]")
        return
    
    example_name = sys.argv[1]
    
    if example_name not in example_map:
        console.print(f"[red]Unknown example: {example_name}[/red]")
        console.print(f"Available: {', '.join(example_map.keys())}")
        return
    
    example_func = example_map[example_name]
    
    if asyncio.iscoroutinefunction(example_func):
        asyncio.run(example_func())
    else:
        example_func()


if __name__ == "__main__":
    main()