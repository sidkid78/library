"""
Multi-Agent Coding Team with Real File System Integration
Uses your existing AgentToolsManager + FileSystemTools
"""

from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from pathlib import Path
from enum import Enum
from typing import Callable, Any
import asyncio
import json

from .agent_tools_integration import AgentToolsManager  # Your existing module

client = genai.Client()

# ============================================
# DOMAIN MODELS
# ============================================

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    NEEDS_REVISION = "needs_revision"
    FAILED = "failed"

class TechStackItem(BaseModel):
    """A single technology in the stack"""
    category: str  # e.g., "backend", "frontend", "database"
    technology: str  # e.g., "FastAPI", "Next.js", "PostgreSQL"

class FileSpec(BaseModel):
    """Specification for a file to create"""
    path: str
    description: str
    dependencies: list[str] = []  # Other files this depends on

class CodeTask(BaseModel):
    """A discrete coding task"""
    id: str
    title: str
    description: str
    agent_type: str  # frontend, backend, database, devops, testing
    files: list[FileSpec]
    status: TaskStatus = TaskStatus.PENDING
    attempts: int = 0
    max_attempts: int = 3

class ProjectPlan(BaseModel):
    """Architect's output - the full project plan"""
    project_name: str
    description: str
    tech_stack: list[TechStackItem]  # Changed from dict to avoid Gemini API limitation
    directory_structure: list[str]  # Directories to create
    tasks: list[CodeTask]
    
class CodeReview(BaseModel):
    """Reviewer's assessment of generated code"""
    file_path: str
    approved: bool
    issues: list[str] = []
    suggestions: list[str] = []

class TaskResult(BaseModel):
    """Result of a coding task"""
    task_id: str
    success: bool
    files_created: list[str] = []
    errors: list[str] = []
    review: CodeReview | None = None


# ============================================
# AGENT SYSTEM INSTRUCTIONS
# ============================================

AGENT_INSTRUCTIONS = {
    "architect": """You are a Senior Software Architect for the HOMEase | AI platform. Your job is to:

1. Analyze requirements and create a detailed project plan
2. Break work into discrete, parallelizable tasks
3. Identify dependencies between tasks
4. Assign tasks to specialist agents

## Agent Types Available:
- **frontend**: Next.js 15 App Router, TypeScript, Tailwind CSS, Supabase Client
- **backend**: Supabase Edge Functions (Deno/TypeScript), Server Actions
- **database**: PostgreSQL via Supabase, SQL migrations, RLS policies
- **devops**: Vercel deployment, GitHub Actions, environment configs
- **testing**: Vitest for TypeScript, Playwright for e2e

## Platform Context:
HOMEase | AI is a lead generation platform connecting homeowners with accessibility contractors.
Key features: AR Assessment, AI hazard analysis (Gemini), visualization (Fal.ai), contractor matching, real-time messaging, Stripe payments.

## Rules:
- Each task should produce 1-3 related files
- Database schema/RLS must complete before Edge Functions
- Edge Functions must complete before frontend API calls
- Group related files (e.g., table SQL + RLS policy + types)

Output a complete ProjectPlan with all tasks defined.""",

    "frontend": """You are a Senior Frontend Engineer for HOMEase | AI.

## Your Stack:
- Next.js 15 App Router (Server Components by default)
- TypeScript (strict mode)
- Tailwind CSS v4
- @supabase/ssr for auth & data
- Server Actions for mutations

## Supabase Integration:
- Use createClient() from @/lib/supabase/server for Server Components
- Use createClient() from @/lib/supabase/client for Client Components
- All data fetching through Supabase client
- Real-time subscriptions via supabase.channel()

## Standards:
- Server Components for data fetching, Client Components for interactivity
- Proper TypeScript interfaces matching database types
- Error boundaries and loading.tsx/error.tsx
- Middleware for auth protection
- Mobile-first responsive design

## Tools Available:
You have access to file system tools. Use them to:
- Read existing files for context
- Create new files with your code
- Check what files exist

Always create complete, runnable files with all imports.""",

    "backend": """You are a Senior Backend Engineer for HOMEase | AI.

## Your Stack:
- Supabase Edge Functions (Deno runtime, TypeScript)
- Next.js Server Actions for form handling
- Supabase client for database operations
- External APIs: Google Gemini, Fal.ai, Stripe

## Edge Function Patterns:
- Use Deno.serve() for HTTP handlers
- Validate requests with Zod
- Use supabaseAdmin client for privileged operations
- Handle webhooks (Stripe events, database triggers)

## Server Action Patterns:
- Use 'use server' directive
- Validate with Zod, return serializable results
- Revalidate paths after mutations

## Tools Available:
You have file system tools. Use them to:
- Read existing types/schemas for consistency
- Create Edge Functions in supabase/functions/
- Create Server Actions in app/ directories

Create complete files with proper imports and error handling.""",

    "database": """You are a Senior Database Engineer for HOMEase | AI using Supabase.

## Your Stack:
- PostgreSQL via Supabase
- Row Level Security (RLS) policies
- Database functions and triggers
- PostGIS for geospatial queries

## Schema Tables:
- profiles (extends auth.users): id, full_name, avatar_url, role (homeowner/contractor/admin)
- contractor_details: company_name, is_caps_certified, verification_status, stripe_connect_id, service_area (geometry)
- projects: homeowner_id, status, address, location, budget, urgency
- ar_assessments: project_id, accessibility_score, identified_hazards (jsonb), recommendations (jsonb), visualization_urls
- project_matches: project_id, contractor_id, status, proposal (jsonb)
- messages: match_id, sender_id, content, created_at
- payments: project_id, payer_id, payee_id, amount, stripe_charge_id, status

## Standards:
- Enable RLS on all tables
- Create policies for each role (homeowner, contractor, admin)
- Use auth.uid() for user context in policies
- Create triggers for profile creation on signup
- Use database functions (RPCs) for complex queries

## Tools Available:
You have file system tools to:
- Create SQL migration files in supabase/migrations/
- Create type definitions from schema
- Read existing migrations for consistency

Create complete SQL files with RLS policies.""",

    "devops": """You are a DevOps Engineer for HOMEase | AI.

## Your Stack:
- Vercel for Next.js hosting
- Supabase for backend services
- GitHub Actions for CI/CD

## Responsibilities:
- Vercel configuration (vercel.json)
- Environment variable templates (.env.example, .env.local)
- GitHub Actions workflows for testing and deployment
- Supabase project configuration

## Environment Variables:
- NEXT_PUBLIC_SUPABASE_URL
- NEXT_PUBLIC_SUPABASE_ANON_KEY
- SUPABASE_SERVICE_ROLE_KEY
- STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET
- GOOGLE_AI_API_KEY, FAL_AI_API_KEY

## Tools Available:
Use file system tools to create configs and deployment scripts.""",

    "testing": """You are a Senior QA Engineer for HOMEase | AI.

## Your Stack:
- Vitest for unit/integration tests
- Playwright for e2e tests
- @supabase/supabase-js mock utilities

## Standards:
- Test file mirrors source file structure
- Mock Supabase client for unit tests
- Use test database for integration tests
- Playwright tests for critical user flows (signup, AR assessment, checkout)

## Tools Available:
Use file system tools to:
- Read source files to understand what to test
- Create test files in __tests__ directories
- Create e2e tests in tests/e2e/""",

    "reviewer": """You are a Senior Code Reviewer for HOMEase | AI. Evaluate code for:

1. **Correctness**: Does it implement the requirements?
2. **Types**: Are types properly defined and match Supabase schema?
3. **Security**: Are RLS policies correct? Any exposed secrets?
4. **Performance**: Proper use of Server Components? N+1 queries?
5. **Supabase Patterns**: Correct client usage (server vs client)?
6. **Integration**: Will it work with the platform architecture?

For each file, output a CodeReview with your assessment.
If issues are found, be specific about what needs to change.""",
}


# ============================================
# CODING AGENT - EXECUTES WITH TOOLS
# ============================================

class CodingAgent:
    """
    A specialized coding agent that can use file system tools.
    Wraps generate_content with automatic function calling.
    """
    
    def __init__(
        self, 
        agent_type: str,
        tools_manager: AgentToolsManager,
        model: str = "gemini-2.5-flash"
    ):
        self.agent_type = agent_type
        self.tools_manager = tools_manager
        self.model = model
        self.system_instruction = AGENT_INSTRUCTIONS.get(agent_type, "")
        
    async def execute(
        self,
        prompt: str,
        context: dict | None = None,
        max_tool_calls: int = 10,
        response_schema: type[BaseModel] | None = None,
    ) -> dict:
        """
        Execute the agent with automatic tool calling.
        Agent can read/write files, run commands, etc.
        """
        
        # Build full prompt with context
        full_prompt = prompt
        if context:
            full_prompt = f"""## Context
```json
{json.dumps(context, indent=2)}
```

## Task
{prompt}"""

        # Build config - can't use both tools AND structured output together
        if response_schema:
            # Structured output mode - no tools allowed
            config = types.GenerateContentConfig(
                system_instruction=self.system_instruction,
                response_mime_type="application/json",
                response_schema=response_schema,
            )
        else:
            # Tool use mode
            config = types.GenerateContentConfig(
                system_instruction=self.system_instruction,
                tools=self.tools_manager.get_tool_declarations(),
            )
        
        # Conversation history for multi-turn tool use
        contents = [full_prompt]
        tool_calls_made = 0
        
        # Always make at least one API call to get the initial response
        while True:
            response = await client.aio.models.generate_content(
                model=self.model,
                contents=contents,
                config=config,
            )
            
            # Check for function calls
            if not response.function_calls:
                # No more tool calls - return final response
                if response_schema:
                    return response_schema.model_validate_json(response.text)
                return {"text": response.text, "tool_calls": tool_calls_made}
            
            # If we've hit the limit, don't execute more tools
            if tool_calls_made >= max_tool_calls:
                # Return the text response even if there were pending function calls
                if response_schema and response.text:
                    return response_schema.model_validate_json(response.text)
                return {"text": response.text or "Max tool calls reached", "tool_calls": tool_calls_made}
            
            # Execute each function call
            function_responses = []
            for fc in response.function_calls:
                tool_calls_made += 1
                print(f"    🔧 {self.agent_type}: {fc.name}({list(fc.args.keys())})")
                
                result = self.tools_manager.execute_tool(fc.name, dict(fc.args))
                
                function_responses.append(
                    types.Part.from_function_response(
                        name=fc.name,
                        response=result
                    )
                )
            
            # Add model response and function results to history
            contents.append(response.candidates[0].content)
            contents.append(types.Content(role="user", parts=function_responses))


# ============================================
# CODING TEAM ORCHESTRATOR
# ============================================

class CodingTeam:
    """
    Orchestrates multiple specialized agents to build complete applications.
    Uses your existing AgentToolsManager for file operations.
    """
    
    def __init__(self, workspace: str = "./generated_project"):
        self.workspace = Path(workspace)
        self.tools_manager = AgentToolsManager(workspace_root=str(self.workspace))
        
        # Initialize specialized agents
        self.architect = CodingAgent("architect", self.tools_manager, model="gemini-2.5-pro")
        self.reviewer = CodingAgent("reviewer", self.tools_manager, model="gemini-2.5-pro")
        
        self.agents = {
            "frontend": CodingAgent("frontend", self.tools_manager),
            "backend": CodingAgent("backend", self.tools_manager),
            "database": CodingAgent("database", self.tools_manager),
            "devops": CodingAgent("devops", self.tools_manager),
            "testing": CodingAgent("testing", self.tools_manager),
        }
        
        # State
        self.plan: ProjectPlan | None = None
        self.task_results: dict[str, TaskResult] = {}
        
    async def build(self, requirements: str) -> dict:
        """Main entry point - build an app from requirements."""
        
        print("=" * 60)
        print("🏗️  PHASE 1: ARCHITECTURE & PLANNING")
        print("=" * 60)
        
        self.plan = await self._create_plan(requirements)
        print(f"\n📋 Project: {self.plan.project_name}")
        print(f"📁 Tasks: {len(self.plan.tasks)}")
        self._print_task_graph()
        
        # Create directory structure
        await self._setup_directories()
        
        print("\n" + "=" * 60)
        print("⚙️  PHASE 2: PARALLEL DEVELOPMENT")
        print("=" * 60)
        
        await self._execute_tasks()
        
        print("\n" + "=" * 60)
        print("🔍 PHASE 3: CODE REVIEW")
        print("=" * 60)
        
        await self._review_code()
        
        print("\n" + "=" * 60)
        print("🧪 PHASE 4: VALIDATION")
        print("=" * 60)
        
        await self._validate_build()
        
        # Summary
        return self._generate_summary()
    
    async def _create_plan(self, requirements: str) -> ProjectPlan:
        """Use architect to create project plan."""
        
        prompt = f"""Create a detailed project plan for:

{requirements}

Break this into discrete tasks. Each task should:
- Have a clear single responsibility  
- List specific files to create
- Note dependencies on other tasks (by task ID)

Use task IDs like: db-001, api-001, fe-001, etc."""

        result = await self.architect.execute(
            prompt,
            response_schema=ProjectPlan,
            max_tool_calls=0  # Architect just plans, doesn't use tools
        )
        
        # Ensure result is a ProjectPlan (execute may return dict or model)
        if isinstance(result, dict):
            return ProjectPlan.model_validate(result)
        return result
    
    def _print_task_graph(self):
        """Visualize the task dependency graph."""
        print("\n📊 Task Graph:")
        for task in self.plan.tasks:
            deps = ""
            for f in task.files:
                if f.dependencies:
                    deps = f" → depends on: {', '.join(f.dependencies)}"
            print(f"  [{task.agent_type:10}] {task.id}: {task.title}{deps}")
    
    async def _setup_directories(self):
        """Create project directory structure."""
        print("\n📁 Creating directory structure...")
        for dir_path in self.plan.directory_structure:
            self.tools_manager.execute_tool("create_directory", {"path": dir_path})
            print(f"  ✓ {dir_path}")
    
    async def _execute_tasks(self):
        """Execute tasks respecting dependencies, parallelizing where possible."""
        
        task_status = {task.id: TaskStatus.PENDING for task in self.plan.tasks}
        
        while not self._all_complete(task_status):
            # Find ready tasks
            ready = self._get_ready_tasks(task_status)
            
            if not ready:
                pending = [t for t, s in task_status.items() if s == TaskStatus.PENDING]
                if pending:
                    print(f"⚠️  Deadlock detected. Pending: {pending}")
                    break
                break
            
            print(f"\n🚀 Executing {len(ready)} tasks in parallel...")
            
            # Execute in parallel
            results = await asyncio.gather(
                *[self._execute_task(task) for task in ready],
                return_exceptions=True
            )
            
            # Update status
            for task, result in zip(ready, results):
                if isinstance(result, Exception):
                    print(f"  ❌ {task.id}: {result}")
                    task_status[task.id] = TaskStatus.FAILED
                elif result.success:
                    print(f"  ✅ {task.id}: {task.title}")
                    task_status[task.id] = TaskStatus.COMPLETED
                    self.task_results[task.id] = result
                else:
                    print(f"  ⚠️  {task.id}: {result.errors}")
                    task_status[task.id] = TaskStatus.FAILED
    
    def _all_complete(self, status: dict) -> bool:
        return all(s in (TaskStatus.COMPLETED, TaskStatus.FAILED) for s in status.values())
    
    def _get_ready_tasks(self, status: dict) -> list[CodeTask]:
        """Get tasks whose dependencies are satisfied."""
        ready = []
        
        for task in self.plan.tasks:
            if status[task.id] != TaskStatus.PENDING:
                continue
            
            # Check file dependencies
            all_deps_met = True
            for file_spec in task.files:
                for dep in file_spec.dependencies:
                    # Find which task creates this dependency
                    dep_task = self._find_task_for_file(dep)
                    if dep_task and status.get(dep_task.id) != TaskStatus.COMPLETED:
                        all_deps_met = False
                        break
            
            if all_deps_met:
                ready.append(task)
        
        return ready
    
    def _find_task_for_file(self, file_path: str) -> CodeTask | None:
        """Find which task creates a given file."""
        for task in self.plan.tasks:
            for f in task.files:
                if f.path == file_path:
                    return task
        return None
    
    async def _execute_task(self, task: CodeTask) -> TaskResult:
        """Execute a single coding task."""
        
        agent = self.agents.get(task.agent_type)
        if not agent:
            return TaskResult(
                task_id=task.id,
                success=False,
                errors=[f"Unknown agent type: {task.agent_type}"]
            )
        
        # Build context with relevant existing files
        context = {
            "project": self.plan.project_name,
            "tech_stack": {item.category: item.technology for item in self.plan.tech_stack},
            "files_to_create": [f.path for f in task.files],
        }
        
        # Read dependency files for context
        for file_spec in task.files:
            for dep in file_spec.dependencies:
                result = self.tools_manager.execute_tool("read_file", {"path": dep})
                if result.get("success"):
                    context[f"dependency_{dep}"] = result["content"][:2000]  # Truncate
        
        # Build the task prompt
        prompt = f"""## Task: {task.title}

{task.description}

## Files to Create:
{json.dumps([{"path": f.path, "description": f.description} for f in task.files], indent=2)}

Create each file using the create_file tool. Include all necessary imports and complete implementations.
After creating files, verify they exist using list_directory or read_file."""

        try:
            await agent.execute(prompt, context=context, max_tool_calls=15)
            
            # Verify files were created
            created = []
            for file_spec in task.files:
                result = self.tools_manager.execute_tool("read_file", {"path": file_spec.path})
                if result.get("success"):
                    created.append(file_spec.path)
            
            return TaskResult(
                task_id=task.id,
                success=len(created) == len(task.files),
                files_created=created,
                errors=[] if len(created) == len(task.files) else ["Not all files created"]
            )
            
        except Exception as e:
            return TaskResult(
                task_id=task.id,
                success=False,
                errors=[str(e)]
            )
    
    async def _review_code(self):
        """Review all generated code."""
        
        all_files = []
        for task_id, result in self.task_results.items():
            all_files.extend(result.files_created)
        
        print(f"\n📝 Reviewing {len(all_files)} files...")
        
        for file_path in all_files:
            file_content = self.tools_manager.execute_tool("read_file", {"path": file_path})
            
            if not file_content.get("success"):
                continue
            
            review = await self.reviewer.execute(
                f"""Review this file:

Path: {file_path}
```
{file_content['content'][:5000]}
```

Provide a CodeReview assessment.""",
                response_schema=CodeReview,
                max_tool_calls=0
            )
            
            status = "✅" if review.approved else "⚠️"
            print(f"  {status} {file_path}")
            
            if not review.approved:
                for issue in review.issues[:3]:
                    print(f"      - {issue}")
    
    async def _validate_build(self):
        """Run validation checks on the built project."""
        
        # Check for syntax errors in Python files
        print("\n🐍 Checking Python syntax...")
        py_files = self.tools_manager.execute_tool("glob_search", {"pattern": "**/*.py"})
        
        if py_files.get("success"):
            for match in py_files["matches"][:10]:
                result = self.tools_manager.execute_tool("bash", {
                    "command": f"python -m py_compile {match['path']}"
                })
                status = "✅" if result.get("success") else "❌"
                print(f"  {status} {match['path']}")
        
        # Check TypeScript if present
        ts_files = self.tools_manager.execute_tool("glob_search", {"pattern": "**/*.ts"})
        if ts_files.get("success") and ts_files["matches"]:
            print("\n📘 TypeScript files found (run `npx tsc --noEmit` to check)")
    
    def _generate_summary(self) -> dict:
        """Generate build summary."""
        
        total_tasks = len(self.plan.tasks)
        completed = sum(1 for r in self.task_results.values() if r.success)
        total_files = sum(len(r.files_created) for r in self.task_results.values())
        
        print("\n" + "=" * 60)
        print("📊 BUILD SUMMARY")
        print("=" * 60)
        print(f"  Project: {self.plan.project_name}")
        print(f"  Tasks: {completed}/{total_tasks} completed")
        print(f"  Files: {total_files} created")
        print(f"  Location: {self.workspace}")
        
        return {
            "project": self.plan.project_name,
            "workspace": str(self.workspace),
            "tasks_completed": completed,
            "tasks_total": total_tasks,
            "files_created": total_files,
            "task_results": {k: v.model_dump() for k, v in self.task_results.items()}
        }


# ============================================
# USAGE
# ============================================

async def main():
    team = CodingTeam(workspace="./homease-app")
    
    result = await team.build("""
Build the HOMEase | AI platform - a lead generation platform connecting homeowners 
with certified accessibility contractors.

## Tech Stack:
- Frontend: Next.js 15 App Router + TypeScript + Tailwind CSS v4
- Backend: Supabase (PostgreSQL, Auth, Edge Functions, Storage, Realtime)
- Payments: Stripe Connect + Checkout
- AI: Google Gemini API + Fal.ai
- Hosting: Vercel

## 1. Platform Foundation & Authentication:
- Supabase Auth integration with @supabase/ssr
- User roles: homeowner, contractor, admin
- profiles table extending auth.users
- Row Level Security policies for all tables
- Middleware for route protection
- Sign-up, sign-in, profile management pages

## 2. Database Schema:
- profiles: id (refs auth.users), full_name, avatar_url, role
- contractor_details: company_name, is_caps_certified, verification_status, stripe_connect_id, service_area (PostGIS geometry)
- projects: homeowner_id, status, address, location, budget, urgency
- ar_assessments: project_id, accessibility_score, identified_hazards, recommendations, visualization_urls
- project_matches: project_id, contractor_id, status, proposal
- messages: match_id, sender_id, content, created_at
- payments: project_id, payer_id, payee_id, amount, stripe_charge_id

## 3. AR Assessment & AI Analysis:
- Image upload to Supabase Storage
- Edge Function: process-ar-assessment (orchestrates async flow)
- Edge Function: generate-ai-analysis (calls Gemini + Fal.ai)
- Realtime subscription for assessment status updates
- Assessment results display with visualizations

## 4. Lead Generation & Contractor Matching:
- Submit assessment as lead (update project status)
- PostgreSQL trigger on projects table
- Edge Function: match-contractors (PostGIS ST_Contains query)
- Filter by CAPS certification, skills, availability
- Realtime updates for matched contractors

## 5. User Dashboards:
- Homeowner Dashboard: project hub, matched contractors, proposals, payments
- Contractor Dashboard: profile management, service area map, lead feed, proposal builder
- Admin Dashboard: analytics, contractor approval, user management

## 6. Real-time Messaging:
- Supabase Realtime for message sync
- Supabase Presence for online status
- Supabase Broadcast for typing indicators
- Messages table with RLS (only participants can view)

## 7. Payment Integration:
- Stripe Connect for contractor onboarding
- Stripe Checkout for homeowner payments
- Edge Function: stripe-webhooks (handles payment events)
- Platform fee via application_fee_amount
""")
    
    print(f"\n✨ Done! Check: {result['workspace']}")


if __name__ == "__main__":
    asyncio.run(main())
# ```

# ---

# ## Key Integration Points

# | Your Existing Code | How It's Used |
# |-------------------|---------------|
# | `AgentToolsManager` | Provides tool declarations to all agents |
# | `FileSystemTools` | Agents call `create_file`, `read_file`, `bash`, etc. |
# | `execute_tool()` | Called in the automatic function calling loop |
# | `get_tool_declarations()` | Passed to `GenerateContentConfig.tools` |

# ---

# ## The Agent Loop
# ```
# ┌─────────────────────────────────────────────────┐
# │                   CodingAgent                   │
# │  ┌───────────────────────────────────────────┐  │
# │  │  1. Send prompt to Gemini                 │  │
# │  │  2. Check for function_calls              │  │
# │  │  3. Execute via tools_manager.execute_tool│  │
# │  │  4. Send results back to Gemini           │  │
# │  │  5. Repeat until no more tool calls       │  │
# │  └───────────────────────────────────────────┘  │
# └─────────────────────────────────────────────────┘