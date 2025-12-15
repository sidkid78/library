# Code Agent Cookbook

Use this cookbook when forking to a specialized code generation agent.

## When to Use

- Implementing new features or modules
- Refactoring existing code
- Debugging complex issues
- Writing tests
- Code review and optimization
- Architecture design

## Configuration

```yaml
model: gemini-2.5-pro
thinking_budget: 8192
enable_code_execution: false  # Set true for live testing
enable_search: false  # Set true if researching APIs
```

## System Instruction

The code agent uses this default system instruction:

```
You are an expert software engineer and code architect.

Your strengths:
- Writing clean, efficient, production-ready code
- Debugging complex issues systematically
- Designing scalable architectures
- Following best practices and design patterns

Approach:
1. Understand the full requirements before coding
2. Plan your implementation strategy
3. Write code with clear comments
4. Consider edge cases and error handling
5. Suggest tests where appropriate

Always use modern patterns and the latest stable APIs.
```

## Fork Examples

### Simple Code Task

```python
from tools.agent_fork import AgentForker, ForkConfig, AgentType

forker = AgentForker()
result = forker.fork(ForkConfig(
    task="Implement a binary search tree with insert, delete, and search methods in Python",
    agent_type=AgentType.CODE
))
```

### With Context Handoff

```python
result = forker.fork(ForkConfig(
    task="Add authentication middleware to the API",
    agent_type=AgentType.CODE,
    context_summary="""
    Building a FastAPI REST API for a todo application.
    - Using SQLAlchemy with PostgreSQL
    - Pydantic models defined for User and Todo
    - Basic CRUD endpoints implemented
    - Need JWT-based authentication
    """
))
```

### Heavy Reasoning Task

```python
result = forker.fork(ForkConfig(
    task="Refactor the monolithic service into microservices architecture",
    agent_type=AgentType.CODE,
    thinking_budget=16384,  # Maximum thinking for complex architecture
    model="gemini-2.5-pro"
))
```

## CLI Usage

```bash
# Simple code task
uv run tools/agent_fork.py --task "Write a rate limiter class" --type code

# With custom thinking budget
uv run tools/agent_fork.py --task "Design a plugin system" --type code --thinking 12000

# With context
uv run tools/agent_fork.py --task "Add caching layer" --type code \
    --context "Building a web scraper with requests and BeautifulSoup"
```

## Best Practices

### 1. Provide Clear Requirements

```python
# ❌ Vague
task="Make the code better"

# ✅ Specific
task="""Refactor the UserService class to:
1. Separate database access into a UserRepository
2. Add input validation using Pydantic
3. Implement proper error handling with custom exceptions
4. Add type hints throughout
"""
```

### 2. Include Relevant Context

```python
# ❌ No context
context_summary=None

# ✅ Relevant context
context_summary="""
Tech stack: Python 3.11, FastAPI, SQLAlchemy 2.0, PostgreSQL
Existing patterns: Repository pattern, dependency injection
Coding standards: PEP 8, type hints required, Google-style docstrings
"""
```

### 3. Specify Constraints

```python
task="""Implement a caching layer with these constraints:
- Must be thread-safe
- TTL support required
- Maximum memory: 100MB
- Must integrate with existing Redis instance
"""
```

## Integration with Google GenAI SDK

For advanced usage, you can access the underlying SDK directly:

```python
from google import genai
from google.genai import types

client = genai.Client()

# Create a code-focused chat session
chat = client.chats.create(
    model="gemini-2.5-pro",
    config=types.GenerateContentConfig(
        system_instruction="""You are an expert Python developer.
        Write clean, well-documented code following PEP 8.""",
        thinking_config=types.ThinkingConfig(thinking_budget=8192)
    )
)

# Multi-turn coding conversation
response = chat.send_message("Create a base Repository class")
print(response.text)

response = chat.send_message("Now extend it for UserRepository")
print(response.text)
```

## Output Format

The code agent typically returns:

1. **Analysis**: Understanding of the requirements
2. **Plan**: Implementation approach
3. **Code**: The actual implementation with comments
4. **Tests**: Suggested tests (if applicable)
5. **Notes**: Any assumptions or recommendations

## Error Handling

If the code agent returns an error:

```python
result = forker.fork(config)
if result.status == "error":
    # Try with more thinking budget
    config.thinking_budget = 12000
    result = forker.fork(config)
```

## Parallel Code Tasks

For multi-file implementations:

```python
import asyncio

async def implement_modules():
    forker = AgentForker()
    
    tasks = [
        "Implement the User model with SQLAlchemy",
        "Implement the Todo model with SQLAlchemy", 
        "Implement the UserRepository class",
        "Implement the TodoRepository class",
        "Implement the authentication service"
    ]
    
    result = await forker.swarm_execute(
        tasks=tasks,
        agent_type=AgentType.CODE,
        context_summary="Building a todo API with FastAPI and SQLAlchemy"
    )
    
    return result

result = asyncio.run(implement_modules())
```
