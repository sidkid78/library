from google import genai 
from google.genai import types 
from pathlib import Path 
import importlib.util 

client = genai.Client()

class SkillLoader:
    """Progressive disclosure skill loader for Gemini agents."""

    def __init__(self, skills_dir: str = "skills"):
        self.skills_dir = Path(skills_dir)
        self.loaded_tools = {}

    def get_skill_index(self) -> str:
        """Minimal context - just skill names and summaries."""
        index = []
        for skill_path in self.skills_dir.iterdir():
            if skill_path.is_dir():
                skill_md = skill_path / "skill.md" 
                if skill_md.exists():
                    # Only read first 3 lines (name + summary)
                    lines = skill_md.read_text().split('\n')[:3]
                    index.append(f"- {skill_path.name}: {' '.join(lines)}")
        return "\n".join(index)

    def read_skill(self, skill_name: str) -> str:
        """Load full skill.md when agent decides to use it."""
        skill_md = self.skills_dir / skill_name / "skill.md"
        return skill_md.read_text() if skill_md.exists() else "Skill not found"

    def read_cookbook_recipe(self, skill_name: str, recipe_name: str) -> str:
        """Load specific recipe for the current task."""
        recipe_path = self.skills_dir / skill_name / "cookbook" / f"{recipe_name}.md"
        return recipe_path.read_text() if recipe_path.exists() else "Recipe not found"

    def load_tool(self, skill_name: str, tool_name: str):
        """Dynamically load a tool function."""
        tool_path = self.skills_dir / skill_name / "tools" / f"{tool_name}.py"
        spec = importlib.util.spec_from_file_location(tool_name, tool_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return getattr(module, 'main') # Convention: each tool has a main() 

# Usage
loader = SkillLoader() 

response = client.models.generte_content(
    model="gemini-2.5-flash",
    contents="Set up a new feature branch worktree for the authentication system",
    config=types.GenerateContentConfig(
        system_instruction=f"""You are an agent with access to skills.

Available skills (use read_skill to learn more):
{loader.get_skill_index()}

Workflow:
1. Identify the relevent skill 
2. Read the skill.md for instructions 
3. If needed, read a specific cookbook recipe 
4. Execute the appropriate tools
""",
        tools=[
            loader.read_skill,
            loader.read_cookbook_recipe,
            loader.load_tool("git-worktree-manager", "create_worktree")
        ]
    )
)