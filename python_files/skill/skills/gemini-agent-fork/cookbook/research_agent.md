# Research Agent Cookbook

Use this cookbook when forking to a specialized research agent with Google Search grounding.

## When to Use

- Finding current/recent information
- Researching best practices and patterns
- Comparing technologies or approaches
- Fact-checking and verification
- Documentation lookup
- Market or competitor research

## Configuration

```yaml
model: gemini-2.5-flash
thinking_budget: 2048
enable_search: true  # Google Search grounding enabled
enable_code_execution: false
```

## System Instruction

The research agent uses this default system instruction:

```
You are an expert researcher with access to current information.

Your strengths:
- Finding accurate, up-to-date information
- Synthesizing multiple sources
- Distinguishing reliable from unreliable sources
- Providing well-cited answers

Approach:
1. Search for the most current information
2. Cross-reference multiple sources
3. Prioritize official documentation and primary sources
4. Clearly cite your sources
5. Note any conflicting information
```

## Fork Examples

### Simple Research Task

```python
from tools.agent_fork import AgentForker, ForkConfig, AgentType

forker = AgentForker()
result = forker.fork(ForkConfig(
    task="What are the latest features in Python 3.13?",
    agent_type=AgentType.RESEARCH,
    enable_search=True
))
```

### Technology Comparison

```python
result = forker.fork(ForkConfig(
    task="""Compare FastAPI vs Django for building REST APIs in 2025:
    - Performance benchmarks
    - Ecosystem and community
    - Learning curve
    - Production readiness
    - Best use cases""",
    agent_type=AgentType.RESEARCH,
    enable_search=True
))
```

### Documentation Research

```python
result = forker.fork(ForkConfig(
    task="Find the official documentation for Google GenAI SDK function calling with automatic tool execution",
    agent_type=AgentType.RESEARCH,
    enable_search=True,
    context_summary="Building an AI agent system using Gemini models"
))
```

## CLI Usage

```bash
# Simple research
uv run tools/agent_fork.py --task "Latest Gemini API pricing" --type research --search

# Technology research
uv run tools/agent_fork.py --task "Best practices for LLM caching in 2025" --type research --search

# With context
uv run tools/agent_fork.py --task "Find alternatives to Redis for caching" --type research --search \
    --context "Building a high-throughput API that needs distributed caching"
```

## Google Search Integration

The research agent leverages Google Search grounding:

```python
from google import genai
from google.genai import types

client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="What are the latest developments in AI agents?",
    config=types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())]
    )
)

# Access search metadata
if response.candidates[0].grounding_metadata:
    metadata = response.candidates[0].grounding_metadata
    print(f"Search queries: {metadata.web_search_queries}")
    for chunk in metadata.grounding_chunks:
        print(f"Source: {chunk.web.title} - {chunk.web.uri}")

print(response.text)
```

## Best Practices

### 1. Be Specific About What You Need

```python
# ❌ Too vague
task="Tell me about Kubernetes"

# ✅ Specific
task="""Research Kubernetes horizontal pod autoscaling:
- How does the HPA controller work?
- What metrics can trigger scaling?
- Best practices for setting scaling thresholds
- Common pitfalls to avoid
"""
```

### 2. Request Citations

```python
task="""Research the security best practices for JWT tokens.
Please cite your sources and note the publication date of each source.
Focus on recommendations from 2024 or later.
"""
```

### 3. Handle Time-Sensitive Information

```python
task="""What is the current:
1. LTS version of Node.js
2. Stable version of Python
3. Latest release of PostgreSQL

Note the release dates and any upcoming versions.
"""
```

## Research Patterns

### Comparative Analysis

```python
result = forker.fork(ForkConfig(
    task="""Create a comparison table for vector databases:
    | Feature | Pinecone | Weaviate | Qdrant | Milvus |
    Include: pricing, performance, ease of use, hosting options""",
    agent_type=AgentType.RESEARCH,
    enable_search=True
))
```

### Trend Research

```python
result = forker.fork(ForkConfig(
    task="""Research current trends in AI agent architectures:
    - What patterns are emerging?
    - What frameworks are gaining adoption?
    - What are the key challenges being solved?
    Focus on developments from the past 6 months.""",
    agent_type=AgentType.RESEARCH,
    enable_search=True
))
```

### Documentation Deep Dive

```python
result = forker.fork(ForkConfig(
    task="""Find comprehensive documentation on:
    1. Gemini API context caching - how it works, pricing, limitations
    2. How to implement explicit vs implicit caching
    3. Best practices for cache key design
    
    Provide links to official documentation.""",
    agent_type=AgentType.RESEARCH,
    enable_search=True
))
```

## Parallel Research Tasks

For comprehensive research across multiple topics:

```python
import asyncio

async def comprehensive_research():
    forker = AgentForker()
    
    topics = [
        "Current best practices for API rate limiting",
        "Comparison of message queue systems (RabbitMQ, Kafka, Redis Streams)",
        "Latest developments in serverless computing",
        "AI model serving optimization techniques",
        "GraphQL vs REST in 2025"
    ]
    
    result = await forker.swarm_execute(
        tasks=topics,
        agent_type=AgentType.RESEARCH,
        context_summary="Researching for a microservices architecture decision"
    )
    
    # The consolidated_summary combines all research
    print(result.consolidated_summary)
    return result

result = asyncio.run(comprehensive_research())
```

## Handling Research Results

```python
result = forker.fork(ForkConfig(
    task="Research current AI agent frameworks",
    agent_type=AgentType.RESEARCH,
    enable_search=True
))

# The response includes grounded information
print(f"Status: {result.status}")
print(f"Response:\n{result.response}")

# For structured extraction, you can parse the response
# or use a follow-up structured output request
```

## Combining Research with Code

A common pattern is to research first, then code:

```python
# Step 1: Research
research_result = forker.fork(ForkConfig(
    task="Find the recommended way to implement OAuth2 with FastAPI",
    agent_type=AgentType.RESEARCH,
    enable_search=True
))

# Step 2: Code with research context
code_result = forker.fork(ForkConfig(
    task="Implement OAuth2 authentication for the API",
    agent_type=AgentType.CODE,
    context_summary=f"""
    Research findings on OAuth2 with FastAPI:
    {research_result.response}
    
    Project context: Building a REST API for a todo application
    """
))
```

## Error Handling

```python
result = forker.fork(config)

if result.status == "error":
    # Search might have failed - try without search
    config.enable_search = False
    result = forker.fork(config)
    
    if result.status == "success":
        print("Note: Result without live search, may not be current")
```
