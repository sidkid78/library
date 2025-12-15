# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "google-genai>=1.0.0",
#     "pydantic>=2.0.0",
#     "rich>=13.0.0",
# ]
# ///
"""
HOMEase | AI Orchestrator Runner

This script uses the agent orchestrator to implement the HOMEase | AI
architecture from info2.md autonomously.

Usage:
    uv run run_homease_orchestrator.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add tools directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from tools.orchestrator import AgentOrchestrator, OrchestratorConfig
from tools.agent_tools_integration import AgentToolsManager
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()


async def main():
    """Run the HOMEase implementation orchestrator."""
    
    # Configuration
    WORKSPACE_DIR = Path(__file__).parent / "homease-ai-new"
    INFO2_PATH = Path(__file__).parent / "info2.md"
    
    console.print(Panel(
        f"[bold cyan]HOMEase | AI Orchestrator[/bold cyan]\n\n"
        f"📁 Workspace: {WORKSPACE_DIR}\n"
        f"📄 Architecture: {INFO2_PATH}\n"
        f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        title="🏠 Starting Implementation"
    ))
    
    # Create workspace directory
    WORKSPACE_DIR.mkdir(exist_ok=True)
    console.print(f"[green]✓ Created workspace: {WORKSPACE_DIR}[/green]")
    
    # Read the architecture plan
    if not INFO2_PATH.exists():
        console.print(f"[red]✗ Architecture file not found: {INFO2_PATH}[/red]")
        return
    
    architecture_content = INFO2_PATH.read_text(encoding="utf-8")
    console.print(f"[green]✓ Loaded architecture ({len(architecture_content)} bytes)[/green]")
    
    # Extract key sections for context (truncate to fit token limits)
    # Focus on the database schema and API routes sections
    context_summary = architecture_content[:30000]  # First 30k chars
    
    # Configure orchestrator
    config = OrchestratorConfig(
        max_planning_steps=15,
        parallel_execution=True,
        auto_consolidate=True,
        thinking_budget_planning=4096,
        thinking_budget_execution=2048
    )
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(config=config)
    
    # CRITICAL: Update the tools_manager AND forker to use our workspace
    orchestrator.tools_manager = AgentToolsManager(
        workspace_root=str(WORKSPACE_DIR)
    )
    # Also update the forker's tools_manager!
    orchestrator.forker.tools_manager = orchestrator.tools_manager
    console.print(f"[green]✓ Tools manager configured for: {WORKSPACE_DIR}[/green]")
    
    # Define the implementation goal
    goal = """
Implement the HOMEase | AI platform based on the provided technical architecture.

Create a Next.js 15 App Router application with Supabase backend. Execute these tasks:

## Phase 1: Project Foundation
1. Create package.json with Next.js 15, Supabase, and required dependencies
2. Create next.config.js with proper configuration
3. Create TypeScript configuration (tsconfig.json)

## Phase 2: Supabase Database Schema
Create SQL migration files in supabase/migrations/ for these tables:
- profiles (linked to auth.users)
- homeowners
- contractors  
- specialties
- contractor_specialties
- portfolio_items
- projects
- project_assessments
- proposals
- contracts
- milestones
- payments
- messages
- reviews
- notifications
- admin_logs

## Phase 3: Supabase Client Setup
1. Create lib/supabase/client.ts (browser client)
2. Create lib/supabase/server.ts (server client with cookies)
3. Create lib/supabase/middleware.ts (route protection)

## Phase 4: Authentication
1. Create auth.ts with NextAuth.js v5 configuration
2. Create middleware.ts for route protection
3. Create app/api/auth/[...nextauth]/route.ts

## Phase 5: API Routes
Create API routes in app/api/ for:
- auth/register/route.ts
- auth/login/route.ts  
- projects/route.ts (CRUD)
- contractors/route.ts
- proposals/route.ts
- payments/route.ts (Stripe integration placeholder)

## Phase 6: Core Pages
Create pages in app/ with basic layouts:
- app/page.tsx (Landing)
- app/dashboard/page.tsx
- app/projects/page.tsx
- app/contractors/page.tsx

Use the file system tools to create all files. Focus on complete, working code.
"""
    
    console.print(Panel(
        "[bold]Goal Summary:[/bold]\n" + goal[:500] + "...",
        title="📋 Implementation Goal"
    ))
    
    # Execute the orchestrator
    console.print("\n[bold yellow]🚀 Starting orchestrator execution...[/bold yellow]\n")
    
    try:
        result = await orchestrator.plan_and_execute(
            goal=goal,
            context=context_summary,
            max_steps=12
        )
        
        # Display results
        console.print(Panel(
            f"[bold]Status:[/bold] {result.status}\n"
            f"[bold]Steps Completed:[/bold] {sum(1 for s in result.steps if s.status == 'completed')}/{len(result.steps)}\n"
            f"[bold]Steps Failed:[/bold] {sum(1 for s in result.steps if s.status == 'failed')}",
            title=f"📊 Workflow Complete: {result.plan_id}"
        ))
        
        if result.final_result:
            console.print(Panel(
                Markdown(result.final_result[:3000]),
                title="📝 Final Summary"
            ))
        
        # List created files
        console.print("\n[bold cyan]📁 Files in workspace:[/bold cyan]")
        tree_result = orchestrator.tools_manager.execute_tool("get_project_tree", {"path": ".", "max_depth": 4})
        if tree_result.get("success"):
            console.print(tree_result.get("tree", "No files created"))
        
    except Exception as e:
        console.print(f"[red bold]Error during execution:[/red bold] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
