from google import genai 
from google.genai import types
from pydantic import BaseModel
from skill import Skill

client = genai.Client()

class ForkConfig(BaseModel):
    """Configuration for forking a context to a new agent"""
    summary: str 
    next_prompt: str 
    model: str = "gemini-2.5-flash"
    thinking_budget: int = 1024 

class AgentFork(BaseModel):
    fork_id: str 
    status: str 
    response: str

def create_context_summary(chat_history: list[types.Content]) -> str:
    """Summarize conversation history for handoff"""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            *chat_history,
            "Summarize this conversation concisely for handoff to another agent."
        ],
        config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=512)
        )
    )
    return response.text 

def fork_to_new_agent(config: ForkConfig) -> AgentFork:
    """Fork context to a new Gemini agent instance"""
    # Create new chat summarized context 
    chat = client.chats.create(
        model=config.model,
        config=types.GenerateContentConfig(
            system_instruction=f"""You are continuing work from a previous agent.
            
Previous Context Summary:
{config.summary}

Continue the work based on the user's next request.""",
            thinking_config=types.ThinkingConfig(thinking_budget=config.thinking_budget)
        )
    )

    response = chat.send_message(config.next_prompt)
    return AgentFork(
        fork_id=f"fork_{hash(config.summary)[:8]}",
        status="completed",
        response=response.text 
    )

# Skill registration
    skill = Skill(
        name="fork_to_new_agent",
        description="Fork context to a new Gemini agent instance",
        config_type=ForkConfig,
        handler=fork_to_new_agent
    )
    client.skill.register(skill)

