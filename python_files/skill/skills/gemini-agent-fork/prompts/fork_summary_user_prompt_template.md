# Fork Summary User Prompt Template

This template is used by the base agent to create a structured prompt for the forked agent. The base agent fills in the variables and passes the complete prompt to the new agent instance.

## Template

```yaml
# Context Handoff to Forked Agent
# Generated: {{timestamp}}
# Fork ID: {{fork_id}}

previous_context:
  summary: |
    {{context_summary}}
  
  key_decisions:
    {{#each decisions}}
    - {{this}}
    {{/each}}
  
  artifacts:
    {{#each artifacts}}
    - name: {{name}}
      type: {{type}}
      status: {{status}}
    {{/each}}
  
  current_state: |
    {{current_state}}

handoff:
  from_agent: {{source_agent_type}}
  to_agent: {{target_agent_type}}
  reason: {{handoff_reason}}

user_request: |
  {{next_user_request}}

instructions: |
  You are continuing work from a previous agent session.
  
  1. Review the previous context summary above
  2. Understand the key decisions that have been made
  3. Note any artifacts that exist or were discussed
  4. Complete the user's new request while maintaining consistency
  
  Build on the previous work - don't restart from scratch.
```

## Variable Definitions

| Variable | Description | Example |
|----------|-------------|---------|
| `timestamp` | When the fork was created | `2025-01-15T14:30:00` |
| `fork_id` | Unique identifier for this fork | `fork_143000_001` |
| `context_summary` | Summarized conversation history | "User asked for help building an API..." |
| `decisions` | List of key decisions made | `["Use FastAPI", "PostgreSQL for DB"]` |
| `artifacts` | Files/code/docs mentioned | `[{name: "main.py", type: "code", status: "created"}]` |
| `current_state` | Where the work currently stands | "API endpoints defined, need auth" |
| `source_agent_type` | Type of the originating agent | `general` |
| `target_agent_type` | Type of the forked agent | `code` |
| `handoff_reason` | Why the fork is happening | "Specialized coding needed" |
| `next_user_request` | The task for the forked agent | "Implement JWT authentication" |

## Usage Example

### Input (Base Agent Context)

```
User: "I want to build a REST API for a todo app"
Assistant: "I'll help you build that. Let's use FastAPI with PostgreSQL..."
User: "Sounds good, let's start with the data models"
Assistant: "Here are the Pydantic models for Todo and User..."
User: "Now fork to a code agent to implement the full CRUD endpoints"
```

### Generated Fork Prompt

```yaml
previous_context:
  summary: |
    The user is building a REST API for a todo application. We decided to use
    FastAPI as the framework with PostgreSQL as the database. Pydantic models
    have been defined for Todo (id, title, description, completed, created_at)
    and User (id, email, hashed_password, todos).
  
  key_decisions:
    - Use FastAPI for the REST API framework
    - Use PostgreSQL for the database
    - Pydantic models defined for Todo and User entities
  
  artifacts:
    - name: models.py
      type: code
      status: discussed
  
  current_state: |
    Data models are defined. Ready to implement CRUD endpoints.

handoff:
  from_agent: general
  to_agent: code
  reason: Specialized coding agent needed for implementation

user_request: |
  Implement the full CRUD endpoints for the Todo API including:
  - GET /todos - List all todos
  - POST /todos - Create a new todo
  - GET /todos/{id} - Get a specific todo
  - PUT /todos/{id} - Update a todo
  - DELETE /todos/{id} - Delete a todo
  
  Include proper error handling and status codes.

instructions: |
  You are continuing work from a previous agent session.
  
  1. Review the previous context summary above
  2. Understand the key decisions that have been made
  3. Note any artifacts that exist or were discussed
  4. Complete the user's new request while maintaining consistency
  
  Build on the previous work - don't restart from scratch.
```

## Simplified Version

For quick handoffs, use this minimal template:

```
## Context
{{context_summary}}

## Previous Decisions
{{decisions_list}}

## Your Task
{{next_user_request}}

Continue the work based on the context above.
```

## Best Practices

1. **Keep summaries focused**: Include only information relevant to the next task
2. **Preserve technical details**: Don't lose important implementation specifics
3. **Note commitments**: Include any promises or agreements made
4. **List artifacts**: Help the new agent know what exists
5. **Be explicit about state**: Clearly describe where work stopped
