import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from src.memory.storage import MemoryEntry, AgentMemory, MemoryLane, MemoryStorage
from src.utils.logger import logger

class MemoryPromotionService:
    """
    Handles fact maturation, conflict detection, and supersession.
    Ensures memory governance follows the v5 "Provenance Matters" and 
    "No Silent Deletion" principles.
    """
    
    def __init__(self, storage: Optional[MemoryStorage] = None):
        self.storage = storage or MemoryStorage()

    async def promote_candidate(self, agent_id: str, candidate: Dict[str, Any]) -> str:
        """
        Evaluates a candidate fact and promotes it to Semantic Memory.
        Detects conflicts and marks existing items as superseded if necessary.
        """
        memory = await self.storage.load_memory(agent_id)
        if not memory:
            return "Error: Agent memory not found."

        # 1. Create candidate entry
        new_id = str(uuid.uuid4())
        provenance = candidate.get("provenance", {})
        
        # Merge candidate metadata with required fields
        metadata = candidate.get("metadata", {}).copy()
        metadata.update({
            "id": new_id,
            "subject": candidate.get("subject"),
            "source_type": candidate.get("source", "inference")
        })

        new_entry = MemoryEntry(
            role="assistant",
            content=candidate.get("content", ""),
            lane=MemoryLane.SEMANTIC,
            source=candidate.get("source", "inference"),
            confidence=candidate.get("confidence", 0.5),
            provenance=provenance,
            metadata=metadata
        )

        # 2. Conflict Detection (Phase 4 v5)
        # Search semantic memory for contradictions (simplistic key-based for now)
        subject = candidate.get("subject")
        if subject:
            for existing in memory.semantic:
                if existing.superseded_by: continue # Skip already dead facts
                
                existing_subject = existing.metadata.get("subject") if existing.metadata else None
                if existing_subject == subject:
                    # Potential conflict or update
                    logger.info(f"Conflict detected: '{subject}' already exists. Superseding {existing.metadata.get('id')} with {new_id}")
                    existing.superseded_by = new_id
                    # Lower confidence of the old item
                    existing.confidence *= 0.5 

        # 3. Add new entry
        memory.semantic.append(new_entry)
        
        # 4. Persistence
        await self.storage.save_memory(memory)
        return new_id

    async def supersede_item(self, agent_id: str, old_id: str, new_id: str):
        """Manually links an older fact to a newer one."""
        memory = await self.storage.load_memory(agent_id)
        if not memory: return
        
        found = False
        for entry in memory.semantic:
            if entry.metadata and entry.metadata.get("id") == old_id:
                entry.superseded_by = new_id
                found = True
                break
        
        if found:
            await self.storage.save_memory(memory)
            logger.info(f"Manually superseded {old_id} with {new_id}")

# Singleton
promotion_service = MemoryPromotionService()
