---
name: gemini-agent-fork
description: "Fork conversation context to new Gemini agents. Enables parallel agent execution, context handoff, and multi-agent orchestration using Google GenAI SDK."
triggers:
  - fork agent
  - spawn agent
  - new agent
  - parallel agents
  - agent swarm
  - fork context
  - hand off to agent
---

# Gemini Agent Fork Skill

Fork conversation context to specialized Gemini agents for parallel execution and intelligent task routing.

## Purpose

This skill enables you to:

1. **Fork context** to new Gemini agent instances with summarized conversation history
2. **Route tasks** to specialized agents (code, research, analysis, creative)
3. **Execute parallel swarms** for multi-file/multi-task processing
4. **Hand off work** between agents with preserved context

## Variables

```yaml
# Model Configuration
default_model: "gemini-2.5-flash"
code_model: "gemini-2.5-pro"
research_model: "gemini-2.5-flash"
fast_model: "gemini-2.5-flash"
heavy_model: "gemini-2.5-pro"

# Thinking Budgets
default_thinking: 1024
code_thinking: 8192
research_thinking: 2048
fast_thinking: 512

# Feature Flags
enable_parallel_swarm: true
enable_context_caching: true
enable_google_search: true
enable_code_execution: false

# Limits
max_parallel_agents: 10
max_context_tokens: 32000
summary_max_tokens: 2000
```

## Workflow

1. **Understand** the user's request and determine the fork type
2. **Read** the appropriate cookbook documentation based on task type
3. **Summarize** current context if handoff is requested
4. **Execute** the fork using the appropriate tool

## Cookbook Routing

### Code Generation Tasks

If the user requests code generation, refactoring, or complex reasoning:

- **Condition**: Request involves coding, debugging, architecture, or technical implementation
- **Action**: Use the CODE agent type with higher thinking budget
- **Examples**:
  - "Fork an agent to refactor this module"
  - "Spawn a code agent to implement the API"
  - "Hand off to a coding agent for the database layer"

### Research Tasks

If the user requests research, fact-finding, or current information:

- **Condition**: Request involves web search, current events, documentation lookup
- **Action**: Use the RESEARCH agent type with Google Search enabled
- **Examples**:
  - "Fork a research agent to find best practices"
  - "Spawn an agent to research competitor pricing"
  - "Hand off research on the latest SDK features"

### Parallel Execution (Swarm)

If the user requests parallel processing of multiple items:

- **Condition**: Request involves multiple files, batch processing, or parallel tasks
- **Action**: Use swarm_execute with specified concurrency
- **Examples**:
  - "Fork agents to analyze each file in the directory"
  - "Spawn parallel agents for each API endpoint"
  - "Run a swarm to summarize all documents"

## Tools

This skill uses:

- `agent_fork.py` - Primary forking tool
- `context_summarizer.py` - Context compression for handoffs
- `orchestrator.py` - Multi-step workflow coordination

## Quick Start Examples

```python
# Simple fork with context
from tools.agent_fork import AgentForker

forker = AgentForker()
result = forker.fork(
    task="Implement the user authentication module",
    agent_type="code",
    include_context=True,
    context_summary="Working on a FastAPI backend..."
)

# Parallel swarm execution
results = await forker.swarm_execute(
    tasks=["Analyze file1.py", "Analyze file2.py", "Analyze file3.py"],
    agent_type="code"
)

# Research with Google Search
result = forker.fork(
    task="Find the latest Gemini API pricing",
    agent_type="research",
    enable_search=True
)
```
