# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "google-genai>=1.0.0",
#     "pydantic>=2.0.0",
#     "rich>=13.0.0",
# ]
# ///
"""
Context Summarizer for Agent Fork

Summarizes conversation history for efficient context handoff between agents.
Supports various summary styles and token-aware compression.

Usage:
    uv run context_summarizer.py --input conversation.json --style concise
    uv run context_summarizer.py --history "user: hello" "assistant: hi" --style detailed
"""

from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import Optional, Literal
import argparse
import json
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

# Logging setup
from .logging_config import get_logger, log_api_call, log_api_response, log_error, ensure_logging_setup
logger = get_logger('context_summarizer')

console = Console()


class ConversationTurn(BaseModel):
    """A single turn in the conversation"""
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: Optional[str] = None


class ConversationHistory(BaseModel):
    """Full conversation history"""
    turns: list[ConversationTurn]
    metadata: Optional[dict] = None


class ContextSummary(BaseModel):
    """Summarized context for handoff"""
    summary: str
    key_decisions: list[str] = Field(default_factory=list)
    current_task: Optional[str] = None
    open_questions: list[str] = Field(default_factory=list)
    artifacts_mentioned: list[str] = Field(default_factory=list)
    token_count: Optional[int] = None
    compression_ratio: Optional[float] = None
    style: str = "concise"
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class ContextSummarizer:
    """
    Summarize conversation context for agent handoffs.
    
    Provides multiple summary styles optimized for different use cases:
    - concise: Minimal summary for quick handoffs
    - detailed: Comprehensive summary with decisions and context
    - structured: YAML-formatted summary for parsing
    - task_focused: Summary centered on current task state
    """
    
    SUMMARY_PROMPTS = {
        "concise": """Summarize this conversation in 2-3 paragraphs, focusing on:
1. What was discussed
2. What was decided
3. What work remains

Keep it brief but capture the essential context.""",

        "detailed": """Create a comprehensive summary of this conversation including:

1. **Overview**: What is the main topic/goal?
2. **Key Discussions**: What major points were covered?
3. **Decisions Made**: What was agreed upon?
4. **Artifacts**: What files, code, or outputs were created/discussed?
5. **Current State**: Where did the conversation end?
6. **Open Items**: What questions or tasks remain?

Be thorough but avoid redundancy.""",

        "structured": """Summarize this conversation in YAML format:

```yaml
topic: <main topic in one line>
goal: <what the user is trying to accomplish>
context:
  - <key context point 1>
  - <key context point 2>
decisions:
  - <decision 1>
  - <decision 2>
artifacts:
  - name: <artifact name>
    type: <file/code/document>
    status: <created/modified/discussed>
current_state: <where we are now>
next_steps:
  - <next step 1>
  - <next step 2>
open_questions:
  - <question 1>
```

Fill in all fields based on the conversation.""",

        "task_focused": """Summarize the current task state from this conversation:

**Task**: <What is being worked on?>
**Progress**: <What has been completed?>
**Current Step**: <What is happening now?>
**Blockers**: <Any issues or blockers?>
**Next Action**: <What should happen next?>

Focus on actionable information for continuing the work."""
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with GenAI client"""
        import os
        ensure_logging_setup()
        
        logger.info("Initializing ContextSummarizer")
        
        key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        
        if not key:
            logger.error("No API key found - GEMINI_API_KEY not set")
            raise ValueError(
                "GEMINI_API_KEY not set. Export it: export GEMINI_API_KEY='your-key'"
            )
        
        self.client = genai.Client(api_key=key)
        logger.info("ContextSummarizer initialized successfully")
    
    def _format_history(self, history: ConversationHistory) -> str:
        """Format conversation history for the model"""
        formatted = []
        for turn in history.turns:
            role_label = turn.role.upper()
            formatted.append(f"[{role_label}]: {turn.content}")
        return "\n\n".join(formatted)
    
    def _count_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        # Rough estimate: ~4 chars per token
        return len(text) // 4
    
    def summarize(
        self,
        history: ConversationHistory,
        style: Literal["concise", "detailed", "structured", "task_focused"] = "concise",
        max_tokens: int = 2000,
        extract_decisions: bool = True,
        extract_artifacts: bool = True
    ) -> ContextSummary:
        """
        Summarize conversation history for handoff.
        
        Args:
            history: The conversation history to summarize
            style: Summary style (concise, detailed, structured, task_focused)
            max_tokens: Maximum tokens for the summary
            extract_decisions: Whether to extract key decisions separately
            extract_artifacts: Whether to extract mentioned artifacts
            
        Returns:
            ContextSummary with the summarized context
        """
        formatted_history = self._format_history(history)
        original_tokens = self._count_tokens(formatted_history)
        
        logger.info(f"Summarizing conversation: {len(history.turns)} turns, style={style}")
        logger.debug(f"Original content: ~{original_tokens} tokens")
        
        # Get style-specific prompt
        style_prompt = self.SUMMARY_PROMPTS.get(style, self.SUMMARY_PROMPTS["concise"])
        
        # Build the summarization prompt
        prompt = f"""{style_prompt}

## Conversation to Summarize

{formatted_history}

## Instructions
- Keep the summary under {max_tokens} tokens
- Focus on information needed to continue the work
- Preserve important technical details
- Note any commitments or agreements made"""
        
        console.print(Panel(
            f"Summarizing {len(history.turns)} turns...\n"
            f"Style: {style}\n"
            f"Original tokens: ~{original_tokens}",
            title="📝 Context Summarizer"
        ))
        
        log_api_call(logger, "gemini-2.5-flash", prompt[:200], style=style, turns=len(history.turns))
        
        # Generate summary
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=1024)
            )
        )
        
        summary_text = response.text
        summary_tokens = self._count_tokens(summary_text)
        compression_ratio = original_tokens / summary_tokens if summary_tokens > 0 else 0
        
        log_api_response(logger, "gemini-2.5-flash", "success", tokens=summary_tokens)
        logger.info(f"Summary generated: {summary_tokens} tokens, compression={compression_ratio:.1f}x")
        logger.debug(f"Summary preview: {summary_text[:200]}...")
        
        # Extract additional structured information if requested
        key_decisions = []
        artifacts = []
        current_task = None
        open_questions = []
        
        if extract_decisions or extract_artifacts:
            logger.debug("Extracting structured information from summary")
            extraction_prompt = f"""From this conversation summary, extract:

1. KEY_DECISIONS: List each decision or agreement made (one per line, prefix with "- ")
2. ARTIFACTS: List any files, code, or documents mentioned (one per line, prefix with "- ")
3. CURRENT_TASK: The current task being worked on (one line)
4. OPEN_QUESTIONS: Any unresolved questions (one per line, prefix with "- ")

Summary:
{summary_text}

Original conversation:
{formatted_history[:2000]}...

Format your response with clear section headers."""
            
            extraction_response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=extraction_prompt,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_budget=512)
                )
            )
            
            # Parse extraction response
            extraction_text = extraction_response.text
            
            # Simple parsing (could be made more robust)
            lines = extraction_text.split("\n")
            current_section = None
            
            for line in lines:
                line = line.strip()
                if "KEY_DECISIONS" in line.upper() or "DECISIONS" in line.upper():
                    current_section = "decisions"
                elif "ARTIFACTS" in line.upper():
                    current_section = "artifacts"
                elif "CURRENT_TASK" in line.upper():
                    current_section = "task"
                elif "OPEN_QUESTIONS" in line.upper() or "QUESTIONS" in line.upper():
                    current_section = "questions"
                elif line.startswith("- "):
                    item = line[2:].strip()
                    if current_section == "decisions" and extract_decisions:
                        key_decisions.append(item)
                    elif current_section == "artifacts" and extract_artifacts:
                        artifacts.append(item)
                    elif current_section == "questions":
                        open_questions.append(item)
                elif current_section == "task" and line and not line.startswith("#"):
                    current_task = line
        
        logger.info(f"Extraction complete: {len(key_decisions)} decisions, {len(artifacts)} artifacts, {len(open_questions)} questions")
        
        return ContextSummary(
            summary=summary_text,
            key_decisions=key_decisions,
            current_task=current_task,
            open_questions=open_questions,
            artifacts_mentioned=artifacts,
            token_count=summary_tokens,
            compression_ratio=compression_ratio,
            style=style
        )
    
    def summarize_for_fork(
        self,
        history: ConversationHistory,
        next_request: str,
        style: str = "structured"
    ) -> str:
        """
        Create a fork-ready summary with the next request embedded.
        
        This creates a prompt that can be directly passed to a forked agent.
        """
        logger.info(f"Creating fork-ready summary for next request: {next_request[:50]}...")
        summary = self.summarize(history, style=style)
        
        fork_prompt = f"""## Previous Context

{summary.summary}

### Key Decisions Made
{chr(10).join(f"- {d}" for d in summary.key_decisions) if summary.key_decisions else "- None recorded"}

### Current State
{summary.current_task or "No specific task identified"}

### Open Questions
{chr(10).join(f"- {q}" for q in summary.open_questions) if summary.open_questions else "- None"}

---

## Your Task

{next_request}

Use the context above to inform your response. Build on previous decisions and maintain consistency with the work already done."""
        
        return fork_prompt


def main():
    """CLI interface for context summarizer"""
    parser = argparse.ArgumentParser(description="Summarize conversation context")
    parser.add_argument("--input", "-i", type=str, help="JSON file with conversation history")
    parser.add_argument("--history", "-H", nargs="+", help="Inline history (role: content pairs)")
    parser.add_argument("--style", "-s", type=str, default="concise",
                       choices=["concise", "detailed", "structured", "task_focused"])
    parser.add_argument("--max-tokens", type=int, default=2000)
    parser.add_argument("--next-request", "-n", type=str, help="Next request for fork prompt")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    summarizer = ContextSummarizer()
    
    # Build history from input
    if args.input:
        with open(args.input) as f:
            data = json.load(f)
        history = ConversationHistory(**data)
    elif args.history:
        turns = []
        for i, item in enumerate(args.history):
            if ":" in item:
                role, content = item.split(":", 1)
                role = role.strip().lower()
                if role not in ["user", "assistant", "system"]:
                    role = "user" if i % 2 == 0 else "assistant"
            else:
                role = "user" if i % 2 == 0 else "assistant"
                content = item
            turns.append(ConversationTurn(role=role, content=content.strip()))
        history = ConversationHistory(turns=turns)
    else:
        console.print("[red]Provide --input or --history[/red]")
        return
    
    if args.next_request:
        # Create fork-ready prompt
        fork_prompt = summarizer.summarize_for_fork(
            history,
            args.next_request,
            style=args.style
        )
        if args.json:
            print(json.dumps({"fork_prompt": fork_prompt}))
        else:
            console.print(Panel(
                Markdown(fork_prompt),
                title="🔀 Fork-Ready Prompt"
            ))
    else:
        # Just summarize
        summary = summarizer.summarize(
            history,
            style=args.style,
            max_tokens=args.max_tokens
        )
        
        if args.json:
            print(summary.model_dump_json(indent=2))
        else:
            console.print(Panel(
                Markdown(summary.summary),
                title=f"📋 Summary ({summary.style})"
            ))
            if summary.key_decisions:
                console.print(Panel(
                    "\n".join(f"• {d}" for d in summary.key_decisions),
                    title="✅ Key Decisions"
                ))
            console.print(f"\n[dim]Compression: {summary.compression_ratio:.1f}x | "
                         f"Tokens: ~{summary.token_count}[/dim]")


if __name__ == "__main__":
    main()