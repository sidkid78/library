# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "google-genai>=1.0.0",
#     "pydantic>=2.0.0",
#     "rich>=13.0.0",
# ]
# ///
"""Quick test to confirm AgentForker executes tools."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from .tools.agent_fork import AgentForker, ForkConfig, AgentType
from rich.console import Console

console = Console()

def main():
    # Create test workspace
    test_dir = Path(__file__).parent / "test_workspace"
    test_dir.mkdir(exist_ok=True)
    
    console.print(f"[cyan]Testing AgentForker with tools...[/cyan]")
    console.print(f"Workspace: {test_dir}\n")
    
    # Create forker with workspace
    forker = AgentForker(workspace_root=str(test_dir))
    
    # Simple test task
    result = forker.fork(ForkConfig(
        task="Create a file called 'hello.txt' with the content 'Hello from AgentForker!'",
        agent_type=AgentType.CODE,
        enable_tools=True,
        max_tool_turns=5
    ))
    
    console.print(f"\n[bold]Result:[/bold]")
    console.print(f"  Status: {result.status}")
    console.print(f"  Tools executed: {result.tools_executed}")
    console.print(f"  Files created: {result.files_created}")
    
    # Verify file was created
    hello_file = test_dir / "hello.txt"
    if hello_file.exists():
        console.print(f"\n[green]✓ SUCCESS! File created:[/green]")
        console.print(f"  {hello_file}")
        console.print(f"  Content: {hello_file.read_text()}")
    else:
        console.print(f"\n[red]✗ FAILED - File not created[/red]")
        console.print(f"  Response: {result.response[:500]}")

if __name__ == "__main__":
    main()
