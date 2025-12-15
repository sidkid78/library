# General Agent Cookbook

Use this cookbook for general-purpose agent forking and context handoffs.

## When to Use

- Continuing a conversation in a new session
- Handing off work to another agent instance
- Starting fresh with preserved context
- Task delegation without specialization
- Simple assistant tasks

## Configuration

```yaml
model: gemini-2.5-flash
thinking_budget: 1024
enable_search: false
enable_code_execution: false
```

## System Instruction

The general agent uses this default system instruction:

```
You are a helpful AI assistant continuing work from a previous conversation.

You have been provided with a summary of the previous context. Use this to:
1. Understand what has been discussed
2. Continue the work seamlessly
3. Build on previous decisions
4. Maintain consistency with prior agreements
```

## Fork Examples

### Simple Context Handoff

```python
from tools.agent_fork import AgentForker, ForkConfig, AgentType

forker = AgentForker()
result = forker.fork(ForkConfig(
    task="Continue helping me plan my project timeline",
    agent_type=AgentType.GENERAL,
    context_summary="""
    Working on a mobile app project.
    - Decided on React Native for cross-platform
    - Design phase complete
    - Need to plan development sprints
    """
))
```

### Fresh Start with Context

```python
result = forker.fork(ForkConfig(
    task="Let's start working on the database schema",
    agent_type=AgentType.GENERAL,
    context_summary="""
    Building an e-commerce platform.
    Key entities: Users, Products, Orders, Reviews
    Decision: PostgreSQL for relational data
    """
))
```

### Custom System Instruction

```python
result = forker.fork(ForkConfig(
    task="Review my business plan",
    agent_type=AgentType.GENERAL,
    system_instruction="""You are a business consultant with 20 years of experience.
    Provide actionable feedback focusing on:
    - Market viability
    - Financial projections
    - Risk assessment
    Be direct and constructive."""
))
```

## CLI Usage

```bash
# Simple fork
uv run tools/agent_fork.py --task "Help me brainstorm ideas for my app" --type general

# With context
uv run tools/agent_fork.py --task "Continue where we left off" --type general \
    --context "We were designing a REST API for a todo application"

# Output as JSON
uv run tools/agent_fork.py --task "Summarize these requirements" --type general --json
```

## Context Handoff Workflow

### Step 1: Summarize Current Context

```python
from tools.context_summarizer import ContextSummarizer, ConversationHistory, ConversationTurn

summarizer = ContextSummarizer()

# Build history from your conversation
history = ConversationHistory(turns=[
    ConversationTurn(role="user", content="I want to build a todo app"),
    ConversationTurn(role="assistant", content="Great! Let's use FastAPI..."),
    ConversationTurn(role="user", content="What about the database?"),
    ConversationTurn(role="assistant", content="PostgreSQL would be ideal..."),
])

summary = summarizer.summarize(history, style="detailed")
```

### Step 2: Fork with Summary

```python
forker = AgentForker()

result = forker.fork(ForkConfig(
    task="Now let's implement the user authentication",
    agent_type=AgentType.GENERAL,
    context_summary=summary.summary
))
```

### Step 3: Continue in Chat Mode

```python
# For multi-turn continuation, use chat mode
chat = forker.create_chat_fork(
    agent_type=AgentType.GENERAL,
    context_summary=summary.summary
)

# Continue the conversation
response1 = chat.send_message("Let's start with JWT tokens")
print(response1.text)

response2 = chat.send_message("How do we handle token refresh?")
print(response2.text)

# Access full history
for msg in chat.get_history():
    print(f"{msg.role}: {msg.parts[0].text[:100]}...")
```

## Chat Mode vs Single Fork

### Use Single Fork When

- One-shot task completion
- No follow-up expected
- Independent task

```python
# Single fork - one request, one response
result = forker.fork(ForkConfig(
    task="Write a haiku about programming",
    agent_type=AgentType.GENERAL
))
```

### Use Chat Mode When

- Multi-turn conversation expected
- Iterative refinement needed
- Building on previous responses

```python
# Chat mode - ongoing conversation
chat = forker.create_chat_fork(agent_type=AgentType.GENERAL)
r1 = chat.send_message("Let's design a user registration flow")
r2 = chat.send_message("Add email verification to that")
r3 = chat.send_message("What about OAuth options?")
```

## Direct SDK Usage

For maximum control, use the Google GenAI SDK directly:

```python
from google import genai
from google.genai import types

client = genai.Client()

# Single generation
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Help me plan my day",
    config=types.GenerateContentConfig(
        system_instruction="You are a productivity coach.",
        thinking_config=types.ThinkingConfig(thinking_budget=1024)
    )
)
print(response.text)

# Chat session
chat = client.chats.create(
    model="gemini-2.5-flash",
    config=types.GenerateContentConfig(
        system_instruction="You are a helpful assistant."
    )
)

response = chat.send_message("What should I work on first?")
print(response.text)
```

## Best Practices

### 1. Provide Sufficient Context

```python
# ❌ Insufficient
context_summary="We talked about code"

# ✅ Sufficient
context_summary="""
Project: E-commerce API
Stack: FastAPI, PostgreSQL, Redis
Progress: User and Product models complete
Current: Working on Order processing
Decisions: 
- Async order processing with Celery
- Stripe for payments
"""
```

### 2. Clear Task Definition

```python
# ❌ Vague
task="Help me"

# ✅ Clear
task="Help me design the checkout flow for the e-commerce API, including cart management, payment processing, and order confirmation"
```

### 3. Maintain Consistency

```python
# Include key decisions in context to maintain consistency
context_summary="""
Important decisions made:
1. Using TypeScript throughout
2. Following REST conventions
3. All responses in JSON:API format
4. Authentication via JWT

Please maintain these conventions in your responses.
"""
```

## Escalation Patterns

### Escalate to Specialized Agent

```python
# Start with general agent
result = forker.fork(ForkConfig(
    task="What approach should we take for real-time features?",
    agent_type=AgentType.GENERAL
))

# If coding is needed, escalate to code agent
if "implement" in result.response.lower() or "code" in result.response.lower():
    code_result = forker.fork(ForkConfig(
        task="Implement the WebSocket server discussed above",
        agent_type=AgentType.CODE,
        context_summary=result.response
    ))
```

### Escalate Based on Complexity

```python
# Try with fast thinking first
result = forker.fork(ForkConfig(
    task=complex_task,
    agent_type=AgentType.GENERAL,
    thinking_budget=512
))

# If response seems incomplete, retry with more thinking
if len(result.response) < 500 or "I need more" in result.response:
    result = forker.fork(ForkConfig(
        task=complex_task,
        agent_type=AgentType.GENERAL,
        thinking_budget=4096,
        model="gemini-2.5-pro"  # Upgrade model too
    ))
```

## Output Handling

```python
result = forker.fork(config)

# Check status
if result.status == "success":
    print(f"Fork ID: {result.fork_id}")
    print(f"Model: {result.model_used}")
    print(f"Response:\n{result.response}")
    
    # Token usage if available
    if result.total_tokens:
        print(f"Tokens used: {result.total_tokens}")
        
elif result.status == "error":
    print(f"Error: {result.error}")
    # Handle error - retry, escalate, or fail gracefully
```

## Integration with Summarizer

Full workflow combining summarization and forking:

```python
from tools.context_summarizer import ContextSummarizer
from tools.agent_fork import AgentForker, ForkConfig, AgentType

# Summarize existing conversation
summarizer = ContextSummarizer()
fork_prompt = summarizer.summarize_for_fork(
    history=conversation_history,
    next_request="Continue with the implementation phase",
    style="structured"
)

# Fork with the prepared prompt
forker = AgentForker()
result = forker.fork(ForkConfig(
    task=fork_prompt,
    agent_type=AgentType.GENERAL
))
```
