"""
Context-Aware Skill System Package

Provides progressive-disclosure skill management for AI agents.
"""

from .context_aware_skill_system import (
    SkillManager,
    Skill,
    SkillMetadata,
    SkillExecutionResult,
)

__all__ = [
    "SkillManager",
    "Skill",
    "SkillMetadata",
    "SkillExecutionResult",
]
