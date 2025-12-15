# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "google-genai>=1.0.0",
#     "pydantic>=2.0.0",
#     "rich>=13.0.0",
#     "pyyaml>=6.0.0",
# ]
# ///
"""
Context-Aware Skill System

A progressive-disclosure skill system for AI agents that:
- Loads skill metadata efficiently (minimal context)
- Only loads full skill definitions when invoked
- Supports markdown-based skill definitions with YAML frontmatter
- Integrates with AgentToolsManager for file system operations
- Provides comprehensive logging

Usage:
    from skill.context_aware_skill_system import SkillManager
    
    manager = SkillManager(skills_dir=Path("./skills"))
    skill = manager.detect_skill("fork an agent to analyze code")
    if skill:
        result = await manager.execute_skill(skill, user_input, context={})
"""

from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from pathlib import Path
from typing import Optional, Any
import yaml
import re
import json
from datetime import datetime

# Logging setup
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from tools.logging_config import get_logger, ensure_logging_setup
    logger = get_logger('skill_system')
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('skill_system')
    def ensure_logging_setup(): pass

# Try to import AgentToolsManager for tool integration
try:
    from tools.agent_tools_integration import AgentToolsManager
except ImportError:
    AgentToolsManager = None


class SkillMetadata(BaseModel):
    """Level 1: Minimal metadata for skill detection (context efficient)"""
    name: str
    description: str
    triggers: list[str] = Field(default_factory=list)
    

class Skill(BaseModel):
    """Full skill definition - loaded only when invoked"""
    name: str
    description: str
    triggers: list[str] = Field(default_factory=list)
    variables: dict = Field(default_factory=dict)
    workflow: list[str] = Field(default_factory=list)
    system_instruction: Optional[str] = None
    cookbook_path: Optional[Path] = None
    tools_path: Optional[Path] = None
    prompts_dir: Optional[Path] = None
    resources: list[str] = Field(default_factory=list)
    

class SkillExecutionResult(BaseModel):
    """Result from executing a skill"""
    skill_name: str
    success: bool
    response: str
    tokens_used: Optional[int] = None
    execution_time_ms: Optional[int] = None
    error: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class SkillManager:
    """
    Manages skills with progressive disclosure.
    
    Progressive Disclosure:
    - Level 1: Load only metadata for all skills (for detection)
    - Level 2: Load full skill definition only when invoked
    - Level 3: Load cookbook/prompts only when executing
    
    This minimizes context usage while providing rich skill capabilities.
    """
    
    def __init__(
        self, 
        skills_dir: Path,
        workspace_root: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize the SkillManager.
        
        Args:
            skills_dir: Directory containing skill definitions
            workspace_root: Root directory for file operations
            api_key: Optional Gemini API key
        """
        ensure_logging_setup()
        logger.info(f"Initializing SkillManager with skills_dir={skills_dir}")
        
        self.skills_dir = Path(skills_dir)
        self._metadata_cache: dict[str, SkillMetadata] = {}
        self._full_skill_cache: dict[str, Skill] = {}
        
        # Initialize Gemini client
        import os
        key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if key:
            self.client = genai.Client(api_key=key)
            logger.info("Gemini client initialized")
        else:
            self.client = None
            logger.warning("No API key found - skill execution will not work")
        
        # Initialize tools manager if workspace provided
        self.tools_manager = None
        if workspace_root and AgentToolsManager:
            self.tools_manager = AgentToolsManager(workspace_root=workspace_root)
            logger.info(f"AgentToolsManager initialized for {workspace_root}")
        
        # Load skill metadata
        self._load_all_metadata()
        logger.info(f"Loaded {len(self._metadata_cache)} skill(s)")
    
    def _load_all_metadata(self):
        """Level 1: Load only metadata for all skills (context efficient)"""
        if not self.skills_dir.exists():
            logger.warning(f"Skills directory does not exist: {self.skills_dir}")
            return
        
        # Look for skill.md files (markdown format with YAML frontmatter)
        for skill_file in self.skills_dir.glob("*/skill.md"):
            try:
                metadata = self._parse_skill_metadata(skill_file)
                if metadata:
                    self._metadata_cache[metadata.name] = metadata
                    logger.debug(f"Loaded metadata for skill: {metadata.name}")
            except Exception as e:
                logger.error(f"Failed to load skill metadata from {skill_file}: {e}")
        
        # Also look for skill.json files
        for skill_file in self.skills_dir.glob("*/skill.json"):
            try:
                with open(skill_file) as f:
                    data = json.load(f)
                if "metadata" in data:
                    metadata = SkillMetadata(**data["metadata"])
                else:
                    metadata = SkillMetadata(
                        name=data.get("name", skill_file.parent.name),
                        description=data.get("description", ""),
                        triggers=data.get("triggers", data.get("trigger_patterns", []))
                    )
                self._metadata_cache[metadata.name] = metadata
                logger.debug(f"Loaded metadata for skill: {metadata.name}")
            except Exception as e:
                logger.error(f"Failed to load skill from {skill_file}: {e}")
    
    def _parse_skill_metadata(self, skill_file: Path) -> Optional[SkillMetadata]:
        """Parse skill metadata from markdown file with YAML frontmatter"""
        content = skill_file.read_text(encoding='utf-8')
        
        # Extract YAML frontmatter (between --- markers)
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if not frontmatter_match:
            logger.warning(f"No YAML frontmatter found in {skill_file}")
            return None
        
        try:
            frontmatter = yaml.safe_load(frontmatter_match.group(1))
            return SkillMetadata(
                name=frontmatter.get('name', skill_file.parent.name),
                description=frontmatter.get('description', ''),
                triggers=frontmatter.get('triggers', [])
            )
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML frontmatter in {skill_file}: {e}")
            return None
    
    def _parse_skill_full(self, skill_file: Path) -> Optional[Skill]:
        """Level 2: Parse full skill definition from markdown file"""
        content = skill_file.read_text(encoding='utf-8')
        skill_dir = skill_file.parent
        
        # Extract YAML frontmatter
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if not frontmatter_match:
            return None
        
        try:
            frontmatter = yaml.safe_load(frontmatter_match.group(1))
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML in {skill_file}: {e}")
            return None
        
        # Extract markdown body (after frontmatter)
        body = content[frontmatter_match.end():]
        
        # Parse variables section if present
        variables = frontmatter.get('variables', {})
        variables_match = re.search(r'```yaml\s*\n(.*?)\n```', body, re.DOTALL)
        if variables_match:
            try:
                parsed_vars = yaml.safe_load(variables_match.group(1))
                if isinstance(parsed_vars, dict):
                    variables.update(parsed_vars)
            except yaml.YAMLError:
                pass
        
        # Parse workflow steps if present
        workflow = []
        workflow_match = re.search(r'## Workflow\s*\n(.*?)(?=\n##|\Z)', body, re.DOTALL)
        if workflow_match:
            for line in workflow_match.group(1).strip().split('\n'):
                line = line.strip()
                if line.startswith(('1.', '2.', '3.', '4.', '5.', '-', '*')):
                    # Extract the step text
                    step = re.sub(r'^[\d\.\-\*]+\s*', '', line).strip()
                    if step:
                        workflow.append(step)
        
        return Skill(
            name=frontmatter.get('name', skill_dir.name),
            description=frontmatter.get('description', ''),
            triggers=frontmatter.get('triggers', []),
            variables=variables,
            workflow=workflow,
            system_instruction=body,
            cookbook_path=skill_dir / 'cookbook' if (skill_dir / 'cookbook').exists() else None,
            tools_path=skill_dir / 'tools' if (skill_dir / 'tools').exists() else None,
            prompts_dir=skill_dir / 'prompts' if (skill_dir / 'prompts').exists() else None,
            resources=frontmatter.get('resources', [])
        )
    
    def get_skill_summaries(self) -> str:
        """Get minimal skill summaries for system prompts (context efficient)"""
        return "\n".join([
            f"- **{m.name}**: {m.description}"
            for m in self._metadata_cache.values()
        ])
    
    def detect_skill(self, user_input: str) -> Optional[Skill]:
        """
        Detect which skill should handle this input.
        
        Uses trigger patterns from metadata for efficient detection
        without loading full skill definitions.
        """
        user_lower = user_input.lower()
        
        for name, metadata in self._metadata_cache.items():
            for trigger in metadata.triggers:
                if trigger.lower() in user_lower:
                    logger.info(f"Skill '{name}' detected via trigger '{trigger}'")
                    # Load full skill only when detected
                    return self.load_full_skill(name)
        
        logger.debug(f"No skill detected for input: {user_input[:100]}...")
        return None
    
    def load_full_skill(self, name: str) -> Optional[Skill]:
        """Level 2: Load full skill definition (only when needed)"""
        if name in self._full_skill_cache:
            return self._full_skill_cache[name]
        
        # Try markdown format first
        skill_file = self.skills_dir / name / "skill.md"
        if skill_file.exists():
            skill = self._parse_skill_full(skill_file)
            if skill:
                self._full_skill_cache[name] = skill
                logger.debug(f"Loaded full skill: {name}")
                return skill
        
        # Try JSON format
        json_file = self.skills_dir / name / "skill.json"
        if json_file.exists():
            try:
                with open(json_file) as f:
                    data = json.load(f)
                skill = Skill(**data)
                self._full_skill_cache[name] = skill
                logger.debug(f"Loaded full skill from JSON: {name}")
                return skill
            except Exception as e:
                logger.error(f"Failed to load skill {name} from JSON: {e}")
        
        logger.warning(f"Skill not found: {name}")
        return None
    
    def _load_cookbook(self, skill: Skill, user_input: str) -> str:
        """Level 3: Load relevant cookbook documentation for execution"""
        cookbook_content = []
        
        # Load main skill body as cookbook
        if skill.system_instruction:
            cookbook_content.append(skill.system_instruction)
        
        # Load additional cookbook files if they exist
        if skill.cookbook_path and skill.cookbook_path.exists():
            for cookbook_file in skill.cookbook_path.glob("*.md"):
                try:
                    content = cookbook_file.read_text(encoding='utf-8')
                    cookbook_content.append(f"\n## {cookbook_file.stem}\n{content}")
                    logger.debug(f"Loaded cookbook file: {cookbook_file.name}")
                except Exception as e:
                    logger.warning(f"Failed to load cookbook {cookbook_file}: {e}")
        
        # Load relevant prompts based on workflow
        if skill.prompts_dir and skill.prompts_dir.exists():
            for prompt_file in skill.prompts_dir.glob("*.md"):
                try:
                    content = prompt_file.read_text(encoding='utf-8')
                    cookbook_content.append(f"\n### Prompt: {prompt_file.stem}\n{content}")
                except Exception as e:
                    logger.warning(f"Failed to load prompt {prompt_file}: {e}")
        
        return "\n\n".join(cookbook_content)
    
    def _load_tools(self, skill: Skill) -> list[types.Tool]:
        """Load tools for skill execution"""
        tools = []
        
        # If we have AgentToolsManager, use its tools
        if self.tools_manager:
            tools.extend(self.tools_manager.get_tool_declarations())
            logger.debug(f"Loaded {len(tools)} tools from AgentToolsManager")
        
        return tools
    
    async def execute_skill(
        self, 
        skill: Skill, 
        user_input: str, 
        context: dict = None
    ) -> SkillExecutionResult:
        """
        Execute a skill with full context loading.
        
        Args:
            skill: The skill to execute
            user_input: The user's input/request
            context: Additional execution context
            
        Returns:
            SkillExecutionResult with response and metadata
        """
        if not self.client:
            return SkillExecutionResult(
                skill_name=skill.name,
                success=False,
                response="",
                error="No Gemini client available - check API key"
            )
        
        start_time = datetime.now()
        logger.info(f"Executing skill: {skill.name}")
        logger.debug(f"User input: {user_input[:200]}...")
        
        try:
            # Level 3: Load cookbook and tools
            cookbook_content = self._load_cookbook(skill, user_input)
            tools = self._load_tools(skill)
            
            # Build system instruction
            system_instruction = f"""You are executing the **{skill.name}** skill.

## Description
{skill.description}

## Variables
```yaml
{yaml.dump(skill.variables, default_flow_style=False)}
```

## Workflow
{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(skill.workflow))}

## Cookbook Documentation
{cookbook_content}

## Instructions
Follow the workflow steps precisely. Use the available tools when needed.
{f"Additional context: {json.dumps(context)}" if context else ""}
"""
            
            logger.debug(f"System instruction length: {len(system_instruction)} chars")
            
            # Execute with Gemini
            config_dict = {
                "system_instruction": system_instruction,
                "thinking_config": types.ThinkingConfig(thinking_budget=2048)
            }
            
            if tools:
                config_dict["tools"] = tools
            
            response = await self.client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_input,
                config=types.GenerateContentConfig(**config_dict)
            )
            
            # Calculate execution time
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Extract token usage
            tokens = None
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                tokens = getattr(response.usage_metadata, 'total_token_count', None)
            
            logger.info(f"Skill {skill.name} completed in {execution_time}ms, tokens={tokens}")
            
            return SkillExecutionResult(
                skill_name=skill.name,
                success=True,
                response=response.text,
                tokens_used=tokens,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            logger.error(f"Skill execution failed: {e}", exc_info=True)
            return SkillExecutionResult(
                skill_name=skill.name,
                success=False,
                response="",
                error=str(e)
            )
    
    def execute_skill_sync(
        self, 
        skill: Skill, 
        user_input: str, 
        context: dict = None
    ) -> SkillExecutionResult:
        """Synchronous wrapper for execute_skill"""
        import asyncio
        return asyncio.run(self.execute_skill(skill, user_input, context))
    
    def build_agent_system_instruction(self) -> str:
        """Build a system instruction for skill-aware agents"""
        return f"""You are an expert agent with access to specialized skills.

## Available Skills
{self.get_skill_summaries()}

## Behavior
1. Analyze the user's request
2. If a skill matches the task, invoke it by outputting: [INVOKE_SKILL: skill_name]
3. For simple tasks, use tools directly
4. Skills compose multiple tools and sub-prompts for complex workflows

## Important
- Only invoke skills when the task clearly matches
- For ambiguous requests, ask for clarification
- Skills provide specialized knowledge and workflows
"""


# ============================================
# CLI Entry Point
# ============================================

def main():
    """CLI for testing the skill system"""
    import argparse
    import asyncio
    from rich.console import Console
    from rich.panel import Panel
    
    console = Console()
    
    parser = argparse.ArgumentParser(description="Context-Aware Skill System")
    parser.add_argument("--skills-dir", "-s", type=Path, default=Path("./skills"),
                       help="Directory containing skill definitions")
    parser.add_argument("--list", "-l", action="store_true",
                       help="List all available skills")
    parser.add_argument("--detect", "-d", type=str,
                       help="Detect skill for given input")
    parser.add_argument("--execute", "-e", type=str,
                       help="Execute skill with given input")
    parser.add_argument("--skill", type=str,
                       help="Specific skill name to execute (with --execute)")
    
    args = parser.parse_args()
    
    manager = SkillManager(skills_dir=args.skills_dir)
    
    if args.list:
        console.print(Panel(
            manager.get_skill_summaries() or "No skills found",
            title="📚 Available Skills"
        ))
    
    elif args.detect:
        skill = manager.detect_skill(args.detect)
        if skill:
            console.print(Panel(
                f"**Name**: {skill.name}\n"
                f"**Description**: {skill.description}\n"
                f"**Triggers**: {', '.join(skill.triggers)}",
                title=f"🎯 Detected: {skill.name}"
            ))
        else:
            console.print("[yellow]No matching skill detected[/yellow]")
    
    elif args.execute:
        if args.skill:
            skill = manager.load_full_skill(args.skill)
        else:
            skill = manager.detect_skill(args.execute)
        
        if skill:
            result = asyncio.run(manager.execute_skill(skill, args.execute))
            if result.success:
                console.print(Panel(
                    result.response[:2000] + "..." if len(result.response) > 2000 else result.response,
                    title=f"✅ {skill.name} Result"
                ))
                console.print(f"[dim]Tokens: {result.tokens_used}, Time: {result.execution_time_ms}ms[/dim]")
            else:
                console.print(f"[red]Error: {result.error}[/red]")
        else:
            console.print("[red]No skill found to execute[/red]")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()