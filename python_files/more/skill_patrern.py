from google import genai
from google.genai import types
from pydantic import BaseModel
from pathlib import Path
import json

client = genai.Client()

# ============================================
# SKILL DEFINITION PATTERN
# ============================================

class SkillMetadata(BaseModel):
    """Progressive disclosure level 1: Just enough for agent to decide"""
    name: str
    description: str
    trigger_patterns: list[str]  # When should agent invoke this skill
    
class Skill(BaseModel):
    """Full skill definition - loaded only when invoked"""
    metadata: SkillMetadata
    system_instruction: str
    tools: list[str]  # Tool function names this skill can use
    sub_prompts: dict[str, str]  # Composable slash commands within skill
    resources: list[str]  # File paths to additional context

# ============================================
# SKILL REGISTRY - Context Efficient
# ============================================

class SkillRegistry:
    """Manages skills with progressive disclosure - 
    only loads full skill when needed"""
    
    def __init__(self, skills_dir: Path):
        self.skills_dir = skills_dir
        self._metadata_cache: dict[str, SkillMetadata] = {}
        self._load_metadata()
    
    def _load_metadata(self):
        """Level 1: Load only metadata for all skills (context efficient)"""
        for skill_path in self.skills_dir.glob("*/skill.json"):
            with open(skill_path) as f:
                data = json.load(f)
                metadata = SkillMetadata(**data["metadata"])
                self._metadata_cache[metadata.name] = metadata
    
    def get_skill_summaries(self) -> str:
        """What goes in the system prompt - minimal context"""
        return "\n".join([
            f"- {m.name}: {m.description}" 
            for m in self._metadata_cache.values()
        ])
    
    def load_full_skill(self, name: str) -> Skill:
        """Level 2: Load full skill only when invoked"""
        skill_path = self.skills_dir / name / "skill.json"
        with open(skill_path) as f:
            return Skill(**json.load(f))


# ============================================
# ORCHESTRATOR WITH SKILL AWARENESS
# ============================================

class SkillAwareOrchestrator:
    def __init__(self, registry: SkillRegistry, tools: dict):
        self.registry = registry
        self.tools = tools  # All available tool functions
        
    def build_system_instruction(self) -> str:
        return f"""You are an expert agent with access to specialized skills.

## Available Skills (invoke by name when task matches):
{self.registry.get_skill_summaries()}

## Behavior:
1. Analyze the task
2. If a skill matches, invoke it by outputting: [INVOKE_SKILL: skill_name]
3. For simple tasks, use tools directly
4. Skills can compose multiple tools and sub-prompts
"""

    async def run(self, user_message: str):
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=self.build_system_instruction(),
                tools=list(self.tools.values()),
            )
        )
        
        # Check if agent wants to invoke a skill
        if "[INVOKE_SKILL:" in response.text:
            skill_name = self._extract_skill_name(response.text)
            return await self._execute_skill(skill_name, user_message)
        
        return response
    
    async def _execute_skill(self, skill_name: str, context: str):
        """Load full skill and execute with its specialized config"""
        skill = self.registry.load_full_skill(skill_name)
        
        # Get only the tools this skill needs
        skill_tools = [self.tools[t] for t in skill.tools if t in self.tools]
        
        # Execute with skill's specialized system instruction
        return client.models.generate_content(
            model="gemini-2.5-flash",
            contents=context,
            config=types.GenerateContentConfig(
                system_instruction=skill.system_instruction,
                tools=skill_tools,
            )
        )
# ```

# ---

# ## Concrete Skills You Could Build

# Based on your domains:

# ### 1. **Legal Research Skill** (for lawyerbot)
# ```
# /skills/legal-research/
# ├── skill.json
# ├── prompts/
# │   ├── case_search.md
# │   ├── statute_analysis.md
# │   └── citation_format.md
# └── resources/
#     └── jurisdiction_rules.json
# ```

# ### 2. **HOMEase Assessment Skill**
# ```
# /skills/home-assessment/
# ├── skill.json
# ├── prompts/
# │   ├── lead_analysis.md
# │   ├── accessibility_scoring.md
# │   └── recommendation_generator.md
# └── tools/
#     └── assessment_functions.py
# ```

# ### 3. **Trading Analysis Skill**
# ```
# /skills/trading-sentiment/
# ├── skill.json
# ├── prompts/
# │   ├── sentiment_analysis.md
# │   ├── risk_assessment.md
# │   └── position_sizing.md
# └── resources/
#     └── market_indicators.json