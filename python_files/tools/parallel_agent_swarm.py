import asyncio 
from google import genai 
from google.genai import types 
from .agent_tools_integration import AgentToolsManager 

client = genai.Client() 

# Logging setup
from .logging_config import get_logger, log_api_call, log_api_response, log_error, ensure_logging_setup
logger = get_logger('parallel_agent_swarm')

async def spawn_agent(task: str, agent_id: int) -> dict:
    """Spawn a single agent for a subtask"""
    tools_manager = AgentToolsManager(workspace_root="C:\\Users\\sidki\\source\\repos\\library\\python_files\\more")
    response = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=task,
        config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=1024),
            tools=tools_manager.get_tool_declarations()
        )
    )
    logger.info("Agent {} completed task: {}".format(agent_id, task))
    return {"agent_id": agent_id, "task": task, "result": response.text}

async def swarm_execute(tasks: list[str]) -> list[dict]:
    """Execute multiple tasks in parallel across agent swarm"""
    logger.info("Spawning agents for tasks: {}".format(tasks))
    return await asyncio.gather(*[
        spawn_agent(task, i) for i, task in enumerate(tasks)
    ])

# Usage: Fork work to multiple parallel agents 
async def analyze_codebase(files: list[str]):
    tasks = [f"Analyze this file: {f}" for f in files]
    results = await swarm_execute(tasks)

    # Consolidate results
    consolidation = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            "Consolidate these file analysis into a coherent summary:",
            *[r["result"] for r in results]
        ]
    )
    logger.info("Consolidation complete: {}".format(consolidation.text))
    return consolidation.text 
    

if __name__ == "__main__":
    files = r"C:\Users\sidki\source\repos\library\python_files\more"
    asyncio.run(analyze_codebase(files))
    logger.info(files)

    logger.info("Analysis complete", )