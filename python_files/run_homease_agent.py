# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "google-genai>=1.0.0",
#     "pydantic>=2.0.0",
#     "rich>=13.0.0",
# ]
# ///
"""
HOMEase | AI Implementation Agent

This script uses Gemini with function calling to actually create files
for the HOMEase | AI architecture.

Usage:
    uv run run_homease_agent.py
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from google import genai
from google.genai import types
from .tools.agent_tools_integration import AgentToolsManager
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()


def run_agent_loop(goal: str, context: str, tools_manager: AgentToolsManager, max_turns: int = 30):
    """
    Run an agent loop with function calling to create files.
    """
    import os
    
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set")
    
    client = genai.Client(api_key=api_key)
    
    # Get tool declarations
    tools = tools_manager.get_tool_declarations()
    
    # System instruction
    system_instruction = f"""You are an expert software architect implementing the HOMEase | AI platform.

You have access to file system tools to create files and directories. Use them to implement the architecture.

WORKSPACE: {tools_manager.get_workspace_path()}

IMPORTANT RULES:
1. Use the tools to CREATE actual files, don't just describe what to create
2. Create complete, working code - not placeholders
3. Use relative paths from the workspace root
4. Execute one tool at a time and wait for the result
5. After creating a file, move on to the next task
6. When done with all tasks, say "IMPLEMENTATION COMPLETE"

ARCHITECTURE CONTEXT (from info2.md):
{context[:15000]}
"""
    
    # Build initial messages
    messages = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(goal)]
        )
    ]
    
    turn = 0
    while turn < max_turns:
        turn += 1
        console.print(f"\n[cyan]═══ Turn {turn}/{max_turns} ═══[/cyan]")
        
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=messages,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    tools=tools,
                    thinking_config=types.ThinkingConfig(thinking_budget=2048)
                )
            )
        except Exception as e:
            console.print(f"[red]API Error: {e}[/red]")
            break
        
        # Check for function calls
        if response.candidates and response.candidates[0].content:
            content = response.candidates[0].content
            
            # Add assistant message to history
            messages.append(content)
            
            # Check for function calls in parts
            function_calls = []
            text_parts = []
            
            for part in content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    function_calls.append(part.function_call)
                elif hasattr(part, 'text') and part.text:
                    text_parts.append(part.text)
            
            # Print any text response
            for text in text_parts:
                if "IMPLEMENTATION COMPLETE" in text.upper():
                    console.print("[green bold]✓ Implementation complete![/green bold]")
                    return True
                console.print(Panel(text[:500] + "..." if len(text) > 500 else text, title="🤖 Agent"))
            
            # Execute function calls
            if function_calls:
                function_responses = []
                
                for fc in function_calls:
                    tool_name = fc.name
                    args = dict(fc.args) if fc.args else {}
                    
                    console.print(f"[yellow]📁 Executing: {tool_name}[/yellow]")
                    if tool_name == "create_file":
                        console.print(f"   Path: {args.get('path', 'N/A')}")
                    elif tool_name == "create_directory":
                        console.print(f"   Path: {args.get('path', 'N/A')}")
                    
                    # Execute the tool
                    result = tools_manager.execute_tool(tool_name, args)
                    
                    if result.get("success"):
                        console.print(f"[green]   ✓ Success[/green]")
                    else:
                        console.print(f"[red]   ✗ {result.get('error', 'Unknown error')}[/red]")
                    
                    function_responses.append(
                        types.Part.from_function_response(
                            name=tool_name,
                            response={"result": json.dumps(result)}
                        )
                    )
                
                # Add function responses to messages
                messages.append(types.Content(
                    role="user",
                    parts=function_responses
                ))
            else:
                # No function calls and no completion signal - might be done
                if not text_parts:
                    console.print("[yellow]No response parts, ending loop[/yellow]")
                    break
        else:
            console.print("[yellow]No response content[/yellow]")
            break
    
    return False


def main():
    """Main entry point."""
    
    # Configuration
    WORKSPACE_DIR = Path(__file__).parent / "homease-ai-new"
    INFO2_PATH = Path(__file__).parent / "info2.md"
    
    console.print(Panel(
        f"[bold cyan]HOMEase | AI Implementation Agent[/bold cyan]\n\n"
        f"📁 Workspace: {WORKSPACE_DIR}\n"
        f"📄 Architecture: {INFO2_PATH}\n"
        f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        title="🏠 Starting Implementation"
    ))
    
    # Create workspace
    WORKSPACE_DIR.mkdir(exist_ok=True)
    
    # Load architecture
    if not INFO2_PATH.exists():
        console.print(f"[red]✗ Architecture file not found: {INFO2_PATH}[/red]")
        return
    
    architecture = INFO2_PATH.read_text(encoding="utf-8")
    console.print(f"[green]✓ Loaded architecture ({len(architecture)} bytes)[/green]")
    
    # Create tools manager
    tools_manager = AgentToolsManager(workspace_root=str(WORKSPACE_DIR))
    console.print(f"[green]✓ Tools manager ready[/green]")
    
    # Define implementation goal
    goal = """
Implement the HOMEase | AI platform. Create these files in order:

1. FIRST: Create the basic project structure
   - package.json with Next.js 15, @supabase/ssr, next-auth@5, stripe dependencies
   - tsconfig.json for TypeScript
   - next.config.js

2. THEN: Create Supabase database migrations in supabase/migrations/
   - 001_profiles.sql: profiles table linked to auth.users
   - 002_contractors.sql: contractors, specialties, contractor_specialties, portfolio_items
   - 003_projects.sql: projects, project_assessments
   - 004_proposals.sql: proposals, contracts, milestones
   - 005_payments.sql: payments, messages
   - 006_admin.sql: reviews, notifications, admin_logs

3. THEN: Create Supabase client files
   - lib/supabase/client.ts (createBrowserClient)
   - lib/supabase/server.ts (createServerClient with cookies)

4. THEN: Create authentication
   - auth.ts (NextAuth.js configuration with Supabase adapter)
   - middleware.ts (route protection)

5. FINALLY: Create key API routes
   - app/api/projects/route.ts
   - app/api/contractors/route.ts

Use create_file and create_directory tools. Create complete, working code.
Start now by creating the directory structure.
"""
    
    # Run the agent
    success = run_agent_loop(
        goal=goal,
        context=architecture,
        tools_manager=tools_manager,
        max_turns=50
    )
    
    # Show results
    console.print("\n" + "═" * 60)
    console.print("[bold]📊 Results[/bold]")
    
    tree_result = tools_manager.execute_tool("get_project_tree", {"path": ".", "max_depth": 4})
    if tree_result.get("success"):
        console.print(tree_result.get("tree", "No files"))
    
    console.print(f"\n[bold]Tool executions:[/bold] {len(tools_manager.tool_execution_log)}")


if __name__ == "__main__":
    main()
