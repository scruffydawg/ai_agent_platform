from typing import Any, Dict, List
from src.skills.base import BaseSkill
from src.memory.knowledge_base import kb_manager
import asyncio

class KnowledgeSearchSkill(BaseSkill):
    """
    Skill for searching the internal Knowledge Hub (RAG).
    Provides access to technical docs, N8N refs, and project history.
    """
    name: str = "search_reference_kb"
    description: str = "Search the high-fidelity Knowledge Base for technical references, N8N node guides, and coding standard documentation."

    def run(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """
        Executes a vector search against the Knowledge Base.
        Returns a list of relevant text snippets and their metadata.
        """
        # Since kb_manager.search_reference is async, we run it in the event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        results = loop.run_until_complete(kb_manager.search_reference(query, limit))
        
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }

knowledge_search_tool = KnowledgeSearchSkill()
