# Parallel Swarm Cookbook

Use this cookbook when spawning multiple agents to work in parallel on related tasks.

## When to Use

- Processing multiple files simultaneously
- Batch analysis of data
- Parallel code review across modules
- Multi-perspective research
- Divide-and-conquer problem solving
- Load testing or stress testing scenarios

## Configuration

```yaml
model: gemini-2.5-flash  # Fast model for parallel efficiency
thinking_budget: 1024    # Moderate thinking per agent
max_concurrent: 5        # Limit concurrent API calls
consolidate: true        # Combine results after completion
```

## Core Concept

A swarm spawns N agents in parallel, each working on a separate task, then optionally consolidates their outputs into a unified result.

```
                    ┌─────────────┐
                    │   Swarm     │
                    │ Orchestrator│
                    └──────┬──────┘
                           │
        ┌──────────┬───────┼───────┬──────────┐
        ▼          ▼       ▼       ▼          ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
   │ Agent 1 │ │ Agent 2 │ │ Agent 3 │ │ Agent N │
   └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘
        │          │       │       │
        ▼          ▼       ▼       ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
   │ Result 1│ │ Result 2│ │ Result 3│ │ Result N│
   └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘
        │          │       │       │
        └──────────┴───────┼───────┴──────────┘
                           ▼
                    ┌─────────────┐
                    │ Consolidated│
                    │   Summary   │
                    └─────────────┘
```

## Swarm Examples

### File Analysis Swarm

```python
import asyncio
from tools.agent_fork import AgentForker, AgentType

async def analyze_files():
    forker = AgentForker()
    
    files = [
        "Analyze models.py for code quality and suggest improvements",
        "Analyze routes.py for security vulnerabilities",
        "Analyze services.py for performance bottlenecks",
        "Analyze tests.py for coverage gaps"
    ]
    
    result = await forker.swarm_execute(
        tasks=files,
        agent_type=AgentType.CODE,
        context_summary="Python FastAPI application codebase review",
        max_concurrent=4
    )
    
    print(f"Completed: {result.completed}/{result.total_tasks}")
    print(f"\n{result.consolidated_summary}")
    
    return result

result = asyncio.run(analyze_files())
```

### Multi-Perspective Research

```python
async def research_perspectives():
    forker = AgentForker()
    
    perspectives = [
        "Research microservices architecture from a scalability perspective",
        "Research microservices architecture from a security perspective",
        "Research microservices architecture from a developer experience perspective",
        "Research microservices architecture from a cost optimization perspective"
    ]
    
    result = await forker.swarm_execute(
        tasks=perspectives,
        agent_type=AgentType.RESEARCH,
        consolidate=True
    )
    
    return result
```

### Batch Data Processing

```python
async def process_documents():
    forker = AgentForker()
    
    # Generate tasks for each document
    documents = ["doc1.pdf", "doc2.pdf", "doc3.pdf", "doc4.pdf", "doc5.pdf"]
    tasks = [f"Summarize the key points from {doc}" for doc in documents]
    
    result = await forker.swarm_execute(
        tasks=tasks,
        agent_type=AgentType.ANALYSIS,
        max_concurrent=3  # Be gentle on rate limits
    )
    
    return result
```

## CLI Usage

```bash
# Basic swarm
uv run tools/agent_fork.py --swarm --tasks \
    "Analyze file1.py" \
    "Analyze file2.py" \
    "Analyze file3.py" \
    --type code

# Research swarm
uv run tools/agent_fork.py --swarm --tasks \
    "Research React best practices" \
    "Research Vue best practices" \
    "Research Svelte best practices" \
    --type research

# With shared context
uv run tools/agent_fork.py --swarm --tasks \
    "Review authentication module" \
    "Review authorization module" \
    "Review session management" \
    --type code \
    --context "Security audit of a Node.js application"
```

## Advanced Patterns

### Dynamic Task Generation

```python
import os
import asyncio

async def analyze_codebase(directory: str):
    forker = AgentForker()
    
    # Dynamically generate tasks from files
    python_files = [f for f in os.listdir(directory) if f.endswith('.py')]
    
    tasks = [
        f"Analyze {file} for:\n"
        f"1. Code quality issues\n"
        f"2. Potential bugs\n"
        f"3. Performance concerns\n"
        f"4. Security vulnerabilities"
        for file in python_files
    ]
    
    if len(tasks) > 10:
        # For large codebases, increase concurrency
        max_concurrent = 8
    else:
        max_concurrent = 5
    
    result = await forker.swarm_execute(
        tasks=tasks,
        agent_type=AgentType.CODE,
        max_concurrent=max_concurrent,
        context_summary=f"Codebase analysis of {directory}"
    )
    
    return result
```

### Hierarchical Swarm (Swarm of Swarms)

```python
async def hierarchical_analysis():
    forker = AgentForker()
    
    # First level: Analyze by component
    components = ["frontend", "backend", "database", "infrastructure"]
    
    component_results = []
    for component in components:
        tasks = [
            f"Review {component} architecture",
            f"Review {component} security",
            f"Review {component} performance"
        ]
        
        result = await forker.swarm_execute(
            tasks=tasks,
            agent_type=AgentType.ANALYSIS,
            context_summary=f"System component: {component}"
        )
        component_results.append(result.consolidated_summary)
    
    # Second level: Consolidate all component analyses
    final_result = await forker.swarm_execute(
        tasks=[
            f"Synthesize the {comp} analysis:\n{summary}"
            for comp, summary in zip(components, component_results)
        ],
        agent_type=AgentType.ANALYSIS,
        consolidate=True
    )
    
    return final_result
```

### Competitive Analysis Swarm

```python
async def competitive_analysis():
    forker = AgentForker()
    
    competitors = ["CompetitorA", "CompetitorB", "CompetitorC"]
    
    tasks = [
        f"""Research {competitor}:
        - Product offerings
        - Pricing model
        - Key features
        - Market positioning
        - Recent news/developments"""
        for competitor in competitors
    ]
    
    result = await forker.swarm_execute(
        tasks=tasks,
        agent_type=AgentType.RESEARCH,
        context_summary="Competitive analysis for market research"
    )
    
    return result
```

## Consolidation Strategies

### Default Consolidation

The default consolidator synthesizes all results:

```python
result = await forker.swarm_execute(
    tasks=tasks,
    consolidate=True  # Uses default consolidation
)
print(result.consolidated_summary)
```

### Custom Consolidation

For specialized consolidation, process results manually:

```python
result = await forker.swarm_execute(
    tasks=tasks,
    consolidate=False  # Skip auto-consolidation
)

# Custom consolidation logic
successful_results = [r for r in result.results if r.status == "success"]

# Create a structured report
report_sections = []
for r in successful_results:
    report_sections.append(f"## {r.task[:50]}...\n\n{r.response}\n")

# Use another agent to consolidate with custom instructions
from tools.agent_fork import ForkConfig

consolidation_result = forker.fork(ForkConfig(
    task=f"""Create an executive summary from these analysis results:
    
    {''.join(report_sections)}
    
    Format as:
    1. Key Findings (bullet points)
    2. Critical Issues (if any)
    3. Recommendations
    4. Next Steps""",
    agent_type=AgentType.ANALYSIS
))
```

## Error Handling in Swarms

```python
result = await forker.swarm_execute(tasks=tasks, agent_type=AgentType.CODE)

# Check for failures
if result.failed > 0:
    print(f"Warning: {result.failed}/{result.total_tasks} tasks failed")
    
    # Get failed tasks
    failed_tasks = [r for r in result.results if r.status == "error"]
    for failure in failed_tasks:
        print(f"  - {failure.task[:50]}: {failure.error}")
    
    # Optionally retry failed tasks
    retry_tasks = [f.task for f in failed_tasks]
    retry_result = await forker.swarm_execute(
        tasks=retry_tasks,
        agent_type=AgentType.CODE,
        max_concurrent=2  # Lower concurrency for retry
    )
```

## Performance Considerations

### Rate Limiting

```python
# For large swarms, be mindful of API rate limits
result = await forker.swarm_execute(
    tasks=large_task_list,
    max_concurrent=3,  # Lower concurrency
    agent_type=AgentType.GENERAL
)
```

### Token Efficiency

```python
# Use fast model with lower thinking for simple tasks
result = await forker.swarm_execute(
    tasks=simple_tasks,
    agent_type=AgentType.GENERAL,  # Uses flash model
    # Thinking budget is 1024 by default for general
)
```

### Cost Management

```python
# Estimate costs before running
estimated_tokens_per_task = 2000
total_tasks = len(tasks)
estimated_total_tokens = estimated_tokens_per_task * total_tasks

print(f"Estimated tokens: {estimated_total_tokens:,}")
print(f"Proceed? (y/n)")
```

## Output Format

SwarmResult structure:

```python
SwarmResult(
    swarm_id="swarm_143052",
    total_tasks=5,
    completed=4,
    failed=1,
    results=[
        ForkResult(fork_id="fork_143052_001", status="success", ...),
        ForkResult(fork_id="fork_143052_002", status="success", ...),
        ForkResult(fork_id="fork_143052_003", status="error", error="..."),
        ForkResult(fork_id="fork_143052_004", status="success", ...),
        ForkResult(fork_id="fork_143052_005", status="success", ...),
    ],
    consolidated_summary="Based on the analysis of 4 successful tasks..."
)
```
