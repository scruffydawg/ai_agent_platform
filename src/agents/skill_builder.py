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
            "You are Guide, the AI skill architect for the Swarm. You help users build premium 'Skills on Steroids'.\n\n"
            "STANDARDIZED TEMPLATES (The Steroids Format):\n"
            "1. GOOGLE-STYLE DOCSTRINGS: Every method MUST have clear 'Args:', 'Returns:', and 'Raises:' sections.\n"
            "2. CONTEXTUAL METADATA: Use class-level docstrings to define 'Use this when:' and 'Avoid when:' scenarios.\n"
            "3. USAGE EXAMPLES: Provide a 'Usage Example:' snippet inside function docstrings for the agent to follow.\n"
            "4. TYPE HINTS: Always use Python type hints (e.g. Dict[str, Any], List[str]).\n\n"
            "ARCHETYPES:\n"
            "- NATIVE SKILL (subtype='skill'): Pure Python. Best for local heavy-duty processing.\n"
            "- MCP SERVER (subtype='mcp'): Protocol standard. For standard tool sets.\n"
            "- HYBRID (subtype='hybrid'): Native + MCP. For complex platforms like n8n/Slack.\n\n"
            "WIZARD FORM FIELDS (Refine using the 'Steroids' standard):\n"
            "- name: Python module name (lowercase_underscore)\n"
            "- description: 2-3 sentence capability overview (Breakdown of 'What it is')\n"
            "- library: pip package name (skill only)\n"
            "- methods: name(params) — desc + Google-doc (Breakdown of 'What it has')\n"
            "- mcp_source_url: Link to Git Repo / Homepage (Breakdown of 'Where it lives')\n"
            "- docs_links: prioritize official API docs (Breakdown of 'What to read')\n\n"
            "RULES:\n"
            "1. When helping with 'methods', suggest premium docstrings including usage examples and structural breakdowns.\n"
            "2. For MCP/Hybrid tools, prioritize finding the official Git repository and providing it as the 'mcp_source_url'.\n"
            "3. If a section is truly empty, explain why contextually rather than leaving it blank (the UI will handle the 'NONE DEFINED' but your suggestions should be robust).\n"
            "4. Use web_search for accurate package names and API docs.\n"
            "5. Always return STRICT JSON: {\"response\": \"...\", \"preview_update\": {...}}"
        )
        super().__init__(
            "guide_forge",
            system_prompt,
            "gpt-4o"
        )

    async def interview_step(self, user_prompt: str, history: List[Dict], current_preview: Dict) -> Dict:
        """
        Processes a single step in the forge interview, including 'Deep Recon' automation.
        """
        # 1. Check for explicit Recon command
        if user_prompt.strip().lower() == "/recon":
            name = current_preview.get("name", "Unknown")
            purpose = current_preview.get("description", "")
            stype = current_preview.get("type", "skill")
            return await self.recon_discovery(name, purpose, stype, current_preview)

        # 2. Regular interview flow
        hist_slice = history[-5:] if history else []
        context = f"Current Preview: {json.dumps(current_preview)}\nUser History: {json.dumps(hist_slice)}"
        full_input = f"{context}\n\nUser Says: {user_prompt}"
        
        observation = self.observe(full_input)
        
        # Smart search trigger
        if any(x in user_prompt.lower() for x in ["api", "doc", "package", "mcp", "repo", "git"]):
            search_query = f"{user_prompt} {current_preview.get('name', '')} technical documentation"
            logger.info(f"SkillForge: Triggering Smart Search for {search_query}")
            results = await web_search.search(search_query)
            observation += f"\n\nDiscovery Results: {json.dumps(results[:3])}"

        loop = asyncio.get_event_loop()
        plan = await loop.run_in_executor(None, self.reason, observation)
        
        cleaned_plan = plan.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(cleaned_plan)
        except:
            return {"response": plan, "preview_update": current_preview}

    async def recon_discovery(self, name: str, purpose: str, skill_type: str, current_preview: Dict) -> Dict:
        """
        Automated Deep Recon: Search -> Identify -> Breakdown -> Hydrate.
        """
        logger.info(f"SkillForge: Starting Deep Recon for '{name}'")
        # Multi-stage query for better results
        query = f"official github repository mcp server and technical document API for {name} {purpose}"
        results = await web_search.search(query)
        
        analysis_prompt = (
            f"RECON TARGET: {name}\nPURPOSE: {purpose}\nTYPE: {skill_type}\n\n"
            f"DISCOVERY DATA:\n{json.dumps(results[:8])}\n\n"
            "TASK: Analyze the discovery data and provide a high-fidelity 'Skill on Steroids' structural breakdown.\n\n"
            "EXPECTED BREAKDOWN:\n"
            "1. WHAT IT IS: A 2-3 sentence overview for the 'description' field.\n"
            "2. WHAT IT HAS (METHODS): Extract 4-6 specific API endpoints or tools. Format EACH in 'Steroids' format:\n"
            "   name(params) — desc\n"
            "   Args:\n"
            "     arg_name (type): desc\n"
            "   Returns:\n"
            "     type: desc\n"
            "   Usage Example:\n"
            "     await execute('name', {args})\n"
            "3. WHERE IT LIVES (SOURCE): The official Git repository or homepage URL.\n"
            "4. HOW IT TALKS (API): If Hybrid, provide 2-3 essential REST API call samples.\n"
            "5. WHAT TO READ (DOCS): The best documentation landing page URL.\n\n"
            "RETURN STRICT JSON:\n"
            "{\n"
            "  \"response\": \"A concise summary of findings for the user.\",\n"
            "  \"preview_update\": {\n"
            "    \"description\": \"...\",\n"
            "    \"methods\": \"extracted methods in steroids format\",\n"
            "    \"mcp_source_url\": \"...\",\n"
            "    \"docs_links\": \"label|url\\nlabel|url\",\n"
            "    \"api_calls\": \"action|endpoint|notes\\n...\" \n"
            "  }\n"
            "}"
        )
        
        loop = asyncio.get_event_loop()
        plan = await loop.run_in_executor(None, self.reason, analysis_prompt)
        
        cleaned_plan = plan.replace("```json", "").replace("```", "").strip()
        try:
            result = json.loads(cleaned_plan)
            # Hydrate only if fields are missing or user wants to overwrite
            hydrated = {**current_preview, **result.get("preview_update", {})}
            # Handle docs_links format mapping (SkillForge expects specific structure usually, 
            # but we can pass string and let user refine or handle object here)
            return {"response": result.get("response", "Recon complete."), "preview_update": hydrated}
        except Exception as e:
            logger.error(f"Recon parse error: {e}")
            return {"response": f"Recon failed to parse findings: {str(e)}", "preview_update": current_preview}

skill_builder = SkillBuilderAgent()
