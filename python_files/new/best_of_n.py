import asyncio
from google import genai 
from google.genai import types 
from pydantic import BaseModel

client = genai.Client()

class Solution(BaseModel):
    approach: str 
    code: str
    confidence: float 
    trade_offs: list[str]

class SolutionSet(BaseModel):
    solutions: list[Solution]
    recommended_index: int 
    recommendation_reason: str 

async def generate_parallel_solutions(problem: str, n: int = 3) -> list[Solution]:
    """Generate N different solutions in parallel."""

    async def single_solution(variation_prompt: str) -> Solution:
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{problem}\n\nApproach hint: {variation_prompt}",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=Solution
            )
        )
        return Solution.model_validate_json(response.text)

    # Different "seeds" for variation
    variations = [
        "Optimize for simplisity and readability",
        "Optimize for performance and efficiency",
        "Optimize for extensibility and maintainability"
    ]

    solutions = await asyncio.gather(*[
        single_solution(v) for v in variations[:n]
    ])
    return solutions 

async def synthesize_best(problem: str, solutions: list[Solution]) -> SolutionSet:
    """Use a judge model to pick the best solution."""
    response = await client.aio.models.generate_content(
        model="gemini-2.5-pro",
        contents=f"""Problem: {problem}
        
        Solutions generated:
        {[s.model_dump() for s in solutions]}

        Analize each solution and recommend the best one.""",
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=SolutionSet,
            thinking_config=types.ThinkingConfig(thinking_budget=2048)
        )
    )
    return SolutionSet.model_validate_json(response.text)
