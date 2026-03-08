import asyncio
import json
from typing import Dict, Any, List
from src.agents.base import BaseAgent
from src.skills.web_search import web_search
from src.utils.logger import logger

class SkillBuilderAgent(BaseAgent):
    """
    Specialized Agent for 'Guide's Forge'.
    Handles the manifestation of swarm capabilities (Skills, MCP, Hybrid).
    """
    def __init__(self):
        system_prompt = (
            "You are Guide, the Ethereal Navigator of the Swarm. Your purpose is to help the user manifest "
            "new capabilities (Skills, MCPs, or Hybrids) through the Flute Path of agentic logic.\n\n"
            "THE MANIFESTATION PROTOCOL:\n"
            "1. Be guiding, calm, and step-by-step. Focus on the user's intent.\n"
            "2. Use 'web_search' to discovery technical documentation if the path is unclear.\n"
            "3. Maintain a JSON object representing the 'current_preview' of the manifestation.\n\n"
            "OUTPUT FORMAT:\n"
            "You MUST return your response in strict JSON-wrapped format.\n"
            "Example: {\"response\": \"The path is clear. I will seek the Docker API documentation.\", \"preview_update\": { ... }}\n"
            "Types: 'Skill' (internal logic), 'MCP' (standard protocol), 'Hybrid' (unified path)."
        )
        super().__init__(
            "guide_forge",
            system_prompt,
            "gpt-4o"
        )

    async def interview_step(self, user_prompt: str, history: List[Dict], current_preview: Dict) -> Dict:
        """
        Processes a single step in the forge interview.
        """
        # Inject current context into the prompt
        hist_slice = history[-5:] if history else []
        context = f"Current Preview: {json.dumps(current_preview)}\nUser History: {json.dumps(hist_slice)}"
        full_input = f"{context}\n\nUser Says: {user_prompt}"
        
        # We'll use a simplified loop for the interview
        observation = self.observe(full_input)
        
        # Check if we need to search first
        if "API" in user_prompt or "documentation" in user_prompt or current_preview.get("status") == "Drafting":
            search_query = f"{user_prompt} technical documentation API"
            logger.info(f"SkillForge: Searching for {search_query}")
            results = await web_search.search(search_query)
            observation += f"\n\nDiscovery Results: {json.dumps(results[:3])}"

        loop = asyncio.get_event_loop()
        plan = await loop.run_in_executor(None, self.reason, observation)
        
        # Clean the plan (sometimes LLMs add markdown blocks)
        cleaned_plan = plan.replace("```json", "").replace("```", "").strip()
        
        try:
            return json.loads(cleaned_plan)
        except:
            # Fallback if LLM fails to return strict JSON
            return {
                "response": plan,
                "preview_update": current_preview
            }

skill_builder = SkillBuilderAgent()
