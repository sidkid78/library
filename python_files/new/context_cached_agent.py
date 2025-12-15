from google import genai 
from google.genai import types

client = genai.Client()

# Create a cached context with your codebase/knowledge
def create_project_cache(project_files: list[str]) -> str:
    """Cache project context for repeated use."""
    parts = [] 
    for file_path in project_files:
        with open(file_path, 'rb') as f:
            content = f.read() 
        parts.append(types.Part.from_bytes(
            data=content,
            mime_type='text/plain'
        ))

    cached_content = client.caches.create(
        model='gemini-2.5-flash',
        config=types.CreateCachedContentConfig(
            contents=[types.Content(role="user", parts=parts)],
            system_instruction="You are an expert on this codebase.",
            display_name='project-context',
            ttl='3600s'
        )
    )
    return cached_content.name 

def focused_worker(cache_name: str, specific_task: str) -> str:
    """Worker uses shared context but stays focused."""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=specific_task,
        config=types.GenerateContentConfig(
            cached_content=cache_name,
            thinking_config=types.ThinkingConfig(thinking_budget=0)
        )
    )
    return response.text # Worker "deleted" doesnt pollute cache 
    