import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.memory.db_engine import AsyncSessionLocal, MemoryConflictModel, MemoryEntryModel
from src.utils.logger import logger
from sqlalchemy.future import select

class GovernanceService:
    """
    Manages memory consistency, conflict resolution, and fact supersession (GUIDE v5).
    """

    async def detect_conflict(self, subject: str, new_entry_id: str, agent_id: str) -> Optional[str]:
        """
        Detects if a new entry conflicts with existing durable memory.
        For Phase 3, we use a simple 'subject' matching heuristic.
        """
        async with AsyncSessionLocal() as session:
            # Look for existing entries on the same subject
            # This would ideally use semantic search, but for MVP we use exact match in metadata or content hints
            stmt = select(MemoryEntryModel).where(
                MemoryEntryModel.agent_id == agent_id,
                MemoryEntryModel.lane == "semantic",
                MemoryEntryModel.superseded_by == None
            )
            res = await session.execute(stmt)
            existing_entries = res.scalars().all()
            
            for entry in existing_entries:
                # Simple example: if the subject is explicitly in metadata
                if entry.meta_data.get("subject") == subject:
                    conflict_id = str(uuid.uuid4())
                    conflict = MemoryConflictModel(
                        id=uuid.UUID(conflict_id),
                        subject=subject,
                        original_id=entry.id,
                        competitor_id=uuid.UUID(new_entry_id),
                        resolution="detected"
                    )
                    session.add(conflict)
                    await session.commit()
                    logger.warning(f"Governance: Conflict detected for '{subject}' between {entry.id} and {new_entry_id}")
                    return conflict_id
        return None

    async def resolve_conflict(self, conflict_id: str, resolution: str):
        """
        Resolves a detected conflict: 'superseded', 'merged', or 'rejected'.
        """
        async with AsyncSessionLocal() as session:
            stmt = select(MemoryConflictModel).where(MemoryConflictModel.id == uuid.UUID(conflict_id))
            res = await session.execute(stmt)
            conflict = res.scalar_one_or_none()
            
            if not conflict:
                return

            conflict.resolution = resolution
            
            if resolution == "superseded":
                # Mark original as superseded by competitor
                stmt = select(MemoryEntryModel).where(MemoryEntryModel.id == conflict.original_id)
                res = await session.execute(stmt)
                original = res.scalar_one_or_none()
                if original:
                    original.superseded_by = str(conflict.competitor_id)
            
            await session.commit()
            logger.info(f"Governance: Conflict {conflict_id} resolved as '{resolution}'")

governance_service = GovernanceService()
