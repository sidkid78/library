from google import genai 
from google.genai import types 
from pydantic import BaseModel 
from typing import Literal 
import asyncio 

client = genai.Client() 

# Structured output for task decomposition
class SubTask(BaseModel):
    agent_role: str 
    task_description: str 
    required_tools: list[str]
    expected_output_schema: str 

class TaskPlan(BaseModel):
    tasks: list[SubTask]
    execution_order: Literal["parallel", "sequential"]
    synthesis_strategy: str 

# The orchestrator decomposes and delegates
async def orchestrator_agent(user_request: str) -> TaskPlan:
    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=f"""You are an orchestrator agent. Decompose this request into
        focused sub-tasks for worker agents. Each worker should have ONE job.

        Request: {user_prompt}""",
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=TaskPlan, 
            thinking_config=types.ThinkingConfig(thinking_budget=1024)
        )
    )
    return TaskPlan.model_validate_json(response.text)

# Focused worker agents (ephemeral - DELETE after use)
async def worker_agent(task: SubTask, tools: list) -> str:
    response = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=task.task_description,
        config=types.GenerateContentConfig(
            tools=tools,
            thinking_config=types.ThinkingConfig(thinking_budget=0) # Fast execution
        )
    )
    return response.text # Worker is "deleted" - context doesn't persist