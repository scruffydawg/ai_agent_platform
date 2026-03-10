from typing import List, Optional, Dict, Any
from src.memory.storage import MemoryStorage, AgentMemory, MemoryEntry, LearningMemory, LearningEntry, MemoryLane
from packages.services.governance_service import governance_service

class MemoryManager:
    """Manages an agent's memory using the 5-lane GUIDE architecture."""
    
    COMPRESS_THRESHOLD = 50

    def __init__(self, agent_id: str, system_prompt: str, storage_format: str = "json", llm_client=None):
        self.agent_id = agent_id
        self.storage_format = storage_format
        self.storage = MemoryStorage()
        self.llm_client = llm_client
        self.system_prompt = system_prompt
        self.memory = None
        self.learning = None

    async def initialize(self):
        """Async initialization of memory and learning."""
        self.learning = await self.storage.load_learning(self.agent_id)
        
        # Try to load existing memory, otherwise initialize new
        loaded_memory = await self.storage.load_memory(self.agent_id)
        if loaded_memory:
            self.memory = loaded_memory
            # Optionally update system prompt if changed
            if self.memory.system_prompt != self.system_prompt:
                self.memory.system_prompt = self.system_prompt
                await self.save()
        else:
            self.memory = AgentMemory(
                agent_id=self.agent_id,
                system_prompt=self.system_prompt
            )
            await self.save()

    async def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None, lane: str = MemoryLane.SESSION):
        """Adds a message to a specific lane and persists it."""
        entry = MemoryEntry(
            role=role, 
            content=content, 
            lane=lane,
            metadata=metadata
        )
        
        if lane == MemoryLane.SESSION:
            self.memory.session.append(entry)
            if self.llm_client and len(self.memory.session) >= self.COMPRESS_THRESHOLD:
                await self.compress_session(self.llm_client, threshold=self.COMPRESS_THRESHOLD)
        elif lane == MemoryLane.WORKING:
            self.memory.working.append(entry)
        elif lane == MemoryLane.RESUME:
            self.memory.resume = entry
        elif lane == MemoryLane.SEMANTIC:
            # Check for conflicts before adding (Phase 3)
            subject = metadata.get("subject") if metadata else None
            if subject:
                # We need a temporary ID to check for conflicts
                import uuid
                temp_id = str(uuid.uuid4())
                conflict_id = await governance_service.detect_conflict(subject, temp_id, self.agent_id)
                if conflict_id:
                    # For now, we auto-resolve as superseded
                    await governance_service.resolve_conflict(conflict_id, "superseded")
            
            self.memory.semantic.append(entry)
        elif lane == MemoryLane.EPISODIC:
            self.memory.episodic.append(entry)
            
        await self.save()

    def get_messages(self, session_limit: int = 20, include_lanes: Optional[List[str]] = None) -> list:
        """
        Retrieves messages from specified lanes.
        Default retrieves System Prompt + Session (limited).
        """
        if include_lanes is None:
            include_lanes = [MemoryLane.SESSION]
            
        messages = [{"role": "system", "content": self.memory.system_prompt}]
        
        # Add Learning Summary if any
        learning_summary = self.get_learning_summary()
        if learning_summary:
            messages.append({"role": "system", "content": learning_summary})

        # Add Working Memory (Priority 1)
        if MemoryLane.WORKING in include_lanes:
            for entry in self.memory.working:
                messages.append({"role": entry.role, "content": f"[WORKING]: {entry.content}"})

        # Add Resume Memory (Priority 2)
        if MemoryLane.RESUME in include_lanes and self.memory.resume:
            messages.append({
                "role": self.memory.resume.role, 
                "content": f"[RESUME]: {self.memory.resume.content}"
            })

        # Add Semantic Memory (Priority 3)
        if MemoryLane.SEMANTIC in include_lanes:
            for entry in self.memory.semantic:
                messages.append({"role": entry.role, "content": f"[KNOWLEDGE]: {entry.content}"})

        # Add Session Memory (Priority 4)
        if MemoryLane.SESSION in include_lanes:
            session_entries = self.memory.session
            if session_limit and session_limit > 0:
                session_entries = session_entries[-session_limit:]
            for entry in session_entries:
                messages.append({"role": entry.role, "content": entry.content})
                
        return messages

    async def save(self):
        """Forces a save to multi-backend storage."""
        await self.storage.save_memory(self.memory)

    async def clear(self, lanes: Optional[List[str]] = None):
        """Clears specific lanes or all if none specified."""
        if lanes is None:
            self.memory.session = []
            self.memory.working = []
            self.memory.resume = None
            # We usually don't clear semantic/episodic automatically
            await self.storage.delete_memory(self.agent_id)
        else:
            if MemoryLane.SESSION in lanes: self.memory.session = []
            if MemoryLane.WORKING in lanes: self.memory.working = []
            if MemoryLane.RESUME in lanes: self.memory.resume = None
            if MemoryLane.SEMANTIC in lanes: self.memory.semantic = []
            if MemoryLane.EPISODIC in lanes: self.memory.episodic = []
            await self.save()

    async def record_user_learn(self, fact: str, context: Optional[str] = None):
        """Records a learned pattern about the user."""
        entry = LearningEntry(fact=fact, context=context)
        self.learning.user_patterns.append(entry)
        await self.storage.save_learning(self.learning)

    async def record_self_learn(self, fact: str, context: Optional[str] = None):
        """Records a learned pattern about the agent's own behavior/tools."""
        entry = LearningEntry(fact=fact, context=context)
        self.learning.self_patterns.append(entry)
        await self.storage.save_learning(self.learning)

    def get_learning_summary(self) -> str:
        """Returns a string summary of learned patterns for prompt injection."""
        summary = []
        if self.learning.user_patterns:
            summary.append("### LEARNED USER PATTERNS")
            for p in self.learning.user_patterns[-5:]: # Top 5 recent
                summary.append(f"- {p.fact}")
        
        if self.learning.self_patterns:
            summary.append("### LEARNED SELF PATTERNS")
            for p in self.learning.self_patterns[-5:]: # Top 5 recent
                summary.append(f"- {p.fact}")
                
        return "\n".join(summary) if summary else ""

    async def compress_session(self, llm_client, threshold: int = 20):
        """Summarizes the oldest messages in the session lane."""
        if len(self.memory.session) <= threshold:
            return False

        chunk_to_summarize = self.memory.session[:-10]
        remaining_messages = self.memory.session[-10:]

        text_to_summarize = "\n".join([f"{e.role}: {e.content}" for e in chunk_to_summarize])
        
        prompt = f"Please summarize the following conversation history concisely while preserving all key facts, names, and technical decisions made:\n\n{text_to_summarize}"
        
        response = await llm_client.generate_async([{"role": "user", "content": prompt}])
        summary = response if isinstance(response, str) else response.get("content", "")
        
        if summary:
            summary_entry = MemoryEntry(
                role="system", 
                content=f"PREVIOUS SESSION SUMMARY: {summary}",
                lane=MemoryLane.SESSION,
                metadata={"type": "summary"}
            )
            self.memory.session = [summary_entry] + remaining_messages
            await self.save()
            return True
            
        return False
