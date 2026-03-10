import json
import yaml
from pathlib import Path
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Dict, Any, Optional

from src.config import MEMORY_DIR
from src.memory.db_engine import MemoryEntryModel, AgentMemoryModel, AsyncSessionLocal
from src.memory.vector_engine import VectorEngine
from src.memory.cache_engine import CacheEngine
from sqlalchemy.future import select
from sqlalchemy import delete
import uuid
from src.llm.client import LLMClient

class MemoryLane(str):
    SESSION = "session"
    WORKING = "working"
    RESUME = "resume"
    SEMANTIC = "semantic"
    EPISODIC = "episodic"

class MemoryEntry(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    role: str
    content: str
    lane: str = MemoryLane.SESSION
    source: str = "user"
    confidence: float = 1.0
    sensitivity: str = "internal" # internal, confidential, public
    provenance: Dict[str, Any] = Field(default_factory=dict) # Source, method, etc.
    superseded_by: Optional[str] = None # UUID reference to newer fact
    schema_version: str = "5.0"
    metadata: Optional[Dict[str, Any]] = None

class LearningEntry(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    fact: str
    context: Optional[str] = None
    relevance_score: float = 1.0
    confidence: float = 1.0
    source: str = "observation"

class LearningMemory(BaseModel):
    agent_id: str
    user_patterns: List[LearningEntry] = []
    self_patterns: List[LearningEntry] = []
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    schema_version: str = "5.0"

class AgentMemory(BaseModel):
    agent_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    system_prompt: str
    task_status: str = "idle" # idle, active, interrupted
    # 5-Lane Architecture
    session: List[MemoryEntry] = []
    working: List[MemoryEntry] = []
    resume: Optional[MemoryEntry] = None
    semantic: List[MemoryEntry] = []
    episodic: List[MemoryEntry] = []
    
    # Legacy support
    entries: List[MemoryEntry] = []
    schema_version: str = "5.0"

class MemoryStorage:
    """Orchestrates memory persistence across Postgres, Qdrant, and Redis (GUIDE v5)."""
    
    def __init__(self, base_dir: Path = MEMORY_DIR):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.vector_engine = VectorEngine()
        self.cache_engine = CacheEngine()
        self.llm_client = LLMClient()

    async def save_memory(self, memory: AgentMemory):
        """Saves AgentMemory to Postgres (Durable), Redis (Hot), and Qdrant (Semantic) with coordination."""
        save_success = {"postgres": False, "redis": False, "qdrant": False}
        all_entries = memory.session + memory.working + memory.semantic + memory.episodic
        if memory.resume:
            all_entries.append(memory.resume)

        # 1. Source of Truth (Postgres)
        try:
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    # Update Agent Meta
                    stmt = select(AgentMemoryModel).where(AgentMemoryModel.agent_id == memory.agent_id)
                    res = await session.execute(stmt)
                    db_agent = res.scalar_one_or_none()
                    
                    if not db_agent:
                        db_agent = AgentMemoryModel(agent_id=memory.agent_id)
                        session.add(db_agent)
                    
                    db_agent.system_prompt = memory.system_prompt
                    db_agent.task_status = memory.task_status
                    db_agent.schema_version = memory.schema_version
                    db_agent.updated_at = datetime.utcnow()

                    # Clean and Re-sync Entries
                    await session.execute(delete(MemoryEntryModel).where(MemoryEntryModel.agent_id == memory.agent_id))
                    
                    for entry in all_entries:
                        db_entry = MemoryEntryModel(
                            agent_id=memory.agent_id,
                            role=entry.role,
                            content=entry.content,
                            lane=entry.lane,
                            source=entry.source,
                            confidence=entry.confidence,
                            provenance=entry.provenance,
                            superseded_by=entry.superseded_by,
                            meta_data=entry.metadata or {}
                        )
                        session.add(db_entry)
            save_success["postgres"] = True
        except Exception as e:
            logger.error(f"MemoryStorage: Postgres SAVE failed: {e}")
            raise # Postgres failure is fatal for the save operation

        # 2. Performance Cache (Redis)
        try:
            await self.cache_engine.set(f"memory:{memory.agent_id}:hot", memory.model_dump(mode="json"))
            save_success["redis"] = True
        except Exception as e:
            logger.warning(f"MemoryStorage: Redis SAVE failed (will fallback to Postgres): {e}")

        # 3. Semantic Index (Qdrant)
        try:
            indexable_lanes = [MemoryLane.SESSION, MemoryLane.SEMANTIC, MemoryLane.EPISODIC]
            to_index = [e for e in all_entries if e.lane in indexable_lanes]
            
            num_to_index = min(len(to_index), 3)
            to_index_subset = to_index[-num_to_index:] if num_to_index > 0 else []
            
            for entry in to_index_subset:
                 vector = await self.llm_client.get_embeddings(entry.content)
                 meta = {
                     "agent_id": memory.agent_id,
                     "role": entry.role,
                     "lane": entry.lane,
                     "timestamp": entry.timestamp.isoformat(),
                     "source": entry.source
                 }
                 await self.vector_engine.upsert_memory(
                     entry_id=str(uuid.uuid4()),
                     vector=vector,
                     metadata=meta
                 )
            save_success["qdrant"] = True
        except Exception as e:
            logger.warning(f"MemoryStorage: Qdrant INDEX failed: {e}")

        if not all(save_success.values()):
            logger.info(f"MemoryStorage: Partial save completed for {memory.agent_id}. Health: {save_success}")

    async def load_memory(self, agent_id: str) -> Optional[AgentMemory]:
        """Loads AgentMemory from Redis (Hot) with Postgres fallback."""
        # Try Redis first
        hot_data = await self.cache_engine.get(f"memory:{agent_id}:hot")
        if hot_data:
            return AgentMemory(**hot_data)

        # Postgres Fallback
        async with AsyncSessionLocal() as session:
            stmt = select(AgentMemoryModel).where(AgentMemoryModel.agent_id == agent_id)
            res = await session.execute(stmt)
            db_agent = res.scalar_one_or_none()
            
            if not db_agent:
                return None
            
            # Load entries
            stmt_entries = select(MemoryEntryModel).where(MemoryEntryModel.agent_id == agent_id)
            res_entries = await session.execute(stmt_entries)
            db_entries = res_entries.scalars().all()
            
            memory = AgentMemory(
                agent_id=agent_id,
                system_prompt=db_agent.system_prompt,
                task_status=db_agent.task_status,
                schema_version=db_agent.schema_version
            )
            
            for e in db_entries:
                entry = MemoryEntry(
                    role=e.role,
                    content=e.content,
                    lane=e.lane,
                    source=e.source,
                    confidence=e.confidence,
                    provenance=e.provenance,
                    superseded_by=e.superseded_by,
                    metadata=e.meta_data
                )
                if e.lane == MemoryLane.SESSION: memory.session.append(entry)
                elif e.lane == MemoryLane.WORKING: memory.working.append(entry)
                elif e.lane == MemoryLane.RESUME: memory.resume = entry
                elif e.lane == MemoryLane.SEMANTIC: memory.semantic.append(entry)
                elif e.lane == MemoryLane.EPISODIC: memory.episodic.append(entry)
            
            return memory

    async def delete_memory(self, agent_id: str):
        """Wipes memory from all backends."""
        async with AsyncSessionLocal() as session:
            async with session.begin():
                await session.execute(delete(MemoryEntryModel).where(MemoryEntryModel.agent_id == agent_id))
                await session.execute(delete(AgentMemoryModel).where(AgentMemoryModel.agent_id == agent_id))
        await self.cache_engine.delete(f"memory:{agent_id}:hot")

    async def save_learning(self, learning: LearningMemory):
        """Saves learning patterns (Phase 2 async)."""
        path = self.base_dir / f"{learning.agent_id}_learning.json"
        learning.updated_at = datetime.utcnow()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(learning.model_dump(mode="json"), f, indent=4)
        
        await self.cache_engine.set(f"learning:{learning.agent_id}:hot", learning.model_dump(mode="json"))

    async def load_learning(self, agent_id: str) -> LearningMemory:
        """Loads learning patterns (Phase 2 async fallback)."""
        # Try Redis
        hot_data = await self.cache_engine.get(f"learning:{agent_id}:hot")
        if hot_data:
            return LearningMemory(**hot_data)

        path = self.base_dir / f"{agent_id}_learning.json"
        if not path.exists():
            return LearningMemory(agent_id=agent_id)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return LearningMemory(**data)
