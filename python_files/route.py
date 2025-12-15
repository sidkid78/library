from google import genai 
from google.genai import types 
from enum import Enum 

client = genai.Client()

class TaskType(Enum):
    CODE_GENERATION = "code"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    CREATIVE = "creative"

# Cookbook-style routing 
AGENT_CONFIGS = {
    TaskType.CODE_GENERATION: {
        "model": "gemini-2.5-pro",
        "thinking_budget": 8192,
        "system_instruction": "You are an expert code generator..."
    },
    TaskType.RESEARCH: {
        "model": "gemini-2.5-flash",
        "thinking_budget": 2048,
        "tools": [types.Tool(google_search=types.GoogleSearch())]
    },
    TaskType.ANALYSIS: {
        "model": "gemini-2.5-pro",
        "thinking_budget": 4096,
        "system_instruction": "You are a data analyst..."
    }
}

def route_task(user_request: str) -> TaskType:
    """Determine which agent configuration to use"""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"Classify this task: {user_request}",
        config=types.GenerateContentConfig(
            response_mime_type="text/x.enum",
            response_schema=TaskType
        )
    )
    return TaskType(response.text)

def execute_with_routing(user_request: str):
    """Route to appropriate agent based on task type"""
    task_type = route_task(user_request)
    config = AGENT_CONFIGS[task_type]

    return client.models.generate_content(
        model=config["model"],
        contents=user_request,
        config=types.GenerateContentConfig(**config)
    )