# Gemini Agent Fork Skill

Fork conversation context to new Gemini agents for parallel execution, specialized task routing, and multi-agent orchestration using the Google GenAI SDK.

## Features

- **🔀 Context Forking**: Hand off work between agents with preserved context
- **🎯 Specialized Agents**: Route tasks to code, research, analysis, or creative agents
- **🐝 Parallel Swarms**: Execute multiple tasks across an agent swarm
- **🎭 Orchestration**: Plan-and-execute, research-then-code, map-reduce workflows
- **📝 Context Summarization**: Efficient context compression for handoffs

## Installation

```bash
# Clone or copy the skill to your skills directory
cp -r gemini-agent-fork /path/to/your/skills/

# Install dependencies (using uv)
cd gemini-agent-fork/claude/skills/gemini-agent-fork/tools
uv sync
```

## Quick Start

### Set API Key

```bash
export GEMINI_API_KEY="your-api-key"
```

### Fork to a Code Agent

```bash
uv run tools/agent_fork.py --task "Write a binary search implementation" --type code
```

### Research with Google Search

```bash
uv run tools/agent_fork.py --task "Latest Python 3.13 features" --type research --search
```

### Parallel Swarm

```bash
uv run tools/agent_fork.py --swarm --tasks \
    "Analyze file1.py" \
    "Analyze file2.py" \
    "Analyze file3.py" \
    --type code
```

### Plan-and-Execute Workflow

```bash
uv run tools/orchestrator.py plan-and-execute --goal "Build a REST API for a todo app"
```

## Architecture

```
gemini-agent-fork/
├── skill.md                 # Main skill definition (triggers, routing, variables)
├── tools/
│   ├── agent_fork.py        # Core forking functionality
│   ├── context_summarizer.py # Context compression for handoffs
│   └── orchestrator.py      # High-level workflow patterns
├── prompts/
│   └── fork_summary_user_prompt.md  # Template for context handoffs
└── cookbook/
    ├── code_agent.md        # Code generation patterns
    ├── research_agent.md    # Research with Google Search
    ├── parallel_swarm.md    # Parallel execution patterns
    └── gemini_agent.md      # General agent usage
```

## Agent Types

| Type | Model | Thinking | Use Case |
|------|-------|----------|----------|
| `code` | gemini-2.5-pro | 8192 | Implementation, refactoring, debugging |
| `research` | gemini-2.5-flash | 2048 | Current info, docs, fact-checking |
| `analysis` | gemini-2.5-pro | 4096 | Data analysis, patterns, insights |
| `creative` | gemini-2.5-flash | 1024 | Ideation, content, brainstorming |
| `general` | gemini-2.5-flash | 1024 | Default, simple tasks, handoffs |

## Python API

### Basic Fork

```python
from tools.agent_fork import AgentForker, ForkConfig, AgentType

forker = AgentForker()

result = forker.fork(ForkConfig(
    task="Implement user authentication with JWT",
    agent_type=AgentType.CODE,
    context_summary="Building a FastAPI backend"
))

print(result.response)
```

### Parallel Swarm

```python
import asyncio

async def analyze_files():
    forker = AgentForker()
    
    result = await forker.swarm_execute(
        tasks=[
            "Review models.py for issues",
            "Review routes.py for issues",
            "Review services.py for issues"
        ],
        agent_type=AgentType.CODE,
        max_concurrent=3
    )
    
    print(f"Completed: {result.completed}/{result.total_tasks}")
    print(result.consolidated_summary)

asyncio.run(analyze_files())
```

### Context Summarization

```python
from tools.context_summarizer import ContextSummarizer, ConversationHistory, ConversationTurn

summarizer = ContextSummarizer()

history = ConversationHistory(turns=[
    ConversationTurn(role="user", content="I want to build an API"),
    ConversationTurn(role="assistant", content="Let's use FastAPI..."),
])

summary = summarizer.summarize(history, style="detailed")
print(summary.summary)
print(f"Compression: {summary.compression_ratio:.1f}x")
```

### Orchestrated Workflows

```python
from tools.orchestrator import AgentOrchestrator

orchestrator = AgentOrchestrator()

# Plan and execute
result = await orchestrator.plan_and_execute(
    goal="Build a user registration system",
    context="Using FastAPI and PostgreSQL"
)

# Research then code
results = await orchestrator.research_then_code(
    research_query="Best practices for password hashing in 2025",
    coding_task="Implement secure password hashing"
)

# Map-reduce
results = await orchestrator.map_reduce(
    items=["file1.py", "file2.py", "file3.py"],
    map_task_template="Analyze {item} for security issues",
    reduce_task="Create a security audit report"
)
```

## Workflow Patterns

### 1. Fork with Context Handoff

```
[Current Agent] → summarize → [Context Summary] → fork → [New Agent]
```

### 2. Parallel Swarm

```
                ┌→ [Agent 1] → Result 1 ─┐
[Orchestrator] ─┼→ [Agent 2] → Result 2 ─┼→ [Consolidation]
                └→ [Agent 3] → Result 3 ─┘
```

### 3. Plan and Execute

```
[Goal] → [Planner Agent] → [Step 1] → [Step 2] → [Step N] → [Final Result]
```

### 4. Research Then Code

```
[Research Query] → [Research Agent + Search] → [Findings] → [Code Agent] → [Implementation]
```

## CLI Reference

### agent_fork.py

```bash
# Single task
uv run agent_fork.py --task "Your task" --type [code|research|analysis|creative|general]

# With options
uv run agent_fork.py --task "Task" --type code \
    --context "Previous context" \
    --model gemini-2.5-pro \
    --thinking 8000 \
    --search \
    --json

# Swarm mode
uv run agent_fork.py --swarm --tasks "task1" "task2" "task3" --type code
```

### context_summarizer.py

```bash
# From JSON file
uv run context_summarizer.py --input conversation.json --style detailed

# Inline history
uv run context_summarizer.py --history "user: hello" "assistant: hi" --style concise

# For fork handoff
uv run context_summarizer.py --input conv.json --next-request "Continue implementation"
```

### orchestrator.py

```bash
# Plan and execute
uv run orchestrator.py plan-and-execute --goal "Build feature X" --context "Using stack Y"

# Research then code
uv run orchestrator.py research-then-code --research "OAuth best practices" --task "Implement OAuth"

# Map-reduce
uv run orchestrator.py map-reduce --items "a" "b" "c" --map-template "Process {item}" --reduce "Summarize"

# Iterative refinement
uv run orchestrator.py iterative --task "Write a poem" --criteria "Must rhyme" --max-iterations 3
```

## Best Practices

1. **Use appropriate agent types** - Code agents for implementation, research for current info
2. **Provide sufficient context** - Include key decisions and constraints
3. **Control concurrency** - Don't overwhelm API rate limits with large swarms
4. **Consolidate results** - Use the built-in consolidation for swarm outputs
5. **Handle errors gracefully** - Check result status and implement retries

## Examples

See the `cookbook/` directory for detailed examples of each pattern:

- `code_agent.md` - Code generation and refactoring
- `research_agent.md` - Research with Google Search grounding
- `parallel_swarm.md` - Multi-agent parallel execution
- `gemini_agent.md` - General purpose and context handoffs

## License

MIT License - See LICENSE file for details.
