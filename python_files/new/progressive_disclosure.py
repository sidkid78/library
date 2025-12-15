from google import genai 
from google.genai import types 
from pathlib import Path 

client = genai.Client() 

# Tool that progressively discloses context 
def read_tool_documentation(tool_name: str) -> str:
    """Read documentation for a specific tool when needed.
    
    Args:
        tool_name: Name of the tool to learn about (e.g., 'git_worktree', 'database_query')
    
    Returns:
        The tool's documentation and usage instructions.
    """
    tool_path = Path(f"tools/{tool_name}/README.md")
    if tool_path.exists():
        return tool_path.read_text()
    return f"Tool '{tool_name}' not found. Available: {list_available_tools()}"

def list_available_tools() -> list[str]:
    """List all available tools without loading their full documentation."""
    return [p.parent.name for p in Path("tools").glob("*/README.md")]

# The agent starts with MINIMAL context - just the tool index 
SYSTEM_INSTRUCTION = """You have access to specialized tools.
IMPORTANT: Only read tool documentation when you need to use that specific tool. 

Available tools: {tools}

Workflow:
1. Identify which tool(s) you need 
2. Call read_tool_documentation() for ONLY tools 
3. Execute the actual tool based on what you learned
"""

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Create a new git worktree for feature development",
    config=types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION.format(tools=list_available_tools()),
        tools=[read_tool_documentation, execute_git_command]
    )
)
