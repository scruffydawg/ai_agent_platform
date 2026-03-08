from src.memory.storage import MemoryStorage, AgentMemory, MemoryEntry

class MemoryManager:
    """Manages an agent's memory, handling context windows and persistence."""
    
    COMPRESS_THRESHOLD = 50

    def __init__(self, agent_id: str, system_prompt: str, storage_format: str = "json", llm_client=None):
        self.agent_id = agent_id
        self.storage_format = storage_format
        self.storage = MemoryStorage()
        self.llm_client = llm_client
        
        # Try to load existing memory, otherwise initialize new
        loaded_memory = self.storage.load_memory(self.agent_id, self.storage_format)
        if loaded_memory:
            self.memory = loaded_memory
            # Optionally update system prompt if changed
            if self.memory.system_prompt != system_prompt:
                self.memory.system_prompt = system_prompt
                self.save()
        else:
            self.memory = AgentMemory(
                agent_id=self.agent_id,
                system_prompt=system_prompt
            )
            self.save()

    def add_message(self, role: str, content: str, metadata: dict = None):
        """Adds a message to the memory and persists it to disk."""
        entry = MemoryEntry(role=role, content=content, metadata=metadata)
        self.memory.entries.append(entry)
        if self.llm_client and len(self.memory.entries) >= self.COMPRESS_THRESHOLD:
            self.compress_history(self.llm_client, threshold=self.COMPRESS_THRESHOLD)
        self.save()

    def get_messages(self, limit: int = None) -> list:
        """Retrieves messages, optionally limiting to the most recent N (context window)."""
        messages = [{"role": "system", "content": self.memory.system_prompt}]
        
        entries = self.memory.entries
        if limit and limit > 0:
            entries = entries[-limit:]
            
        for entry in entries:
            messages.append({"role": entry.role, "content": entry.content})
            
        return messages

    def save(self):
        """Forces a save to disk."""
        self.storage.save_memory(self.memory, self.storage_format)

    def clear(self):
        """Clears current session memory and deletes the persistence file."""
        self.memory.entries = []
        self.storage.delete_memory(self.agent_id, self.storage_format)

    def compress_history(self, llm_client, threshold: int = 20):
        """
        Summarizes the oldest messages if history exceeds a threshold.
        Appends the summary as a new system memory entry.
        """
        if len(self.memory.entries) <= threshold:
            return False

        # Take the oldest N-10 messages to summarize
        chunk_to_summarize = self.memory.entries[:-10]
        remaining_messages = self.memory.entries[-10:]

        text_to_summarize = "\n".join([f"{e.role}: {e.content}" for e in chunk_to_summarize])
        
        prompt = f"Please summarize the following conversation history concisely while preserving all key facts, names, and technical decisions made:\n\n{text_to_summarize}"
        
        summary = llm_client.generate([{"role": "user", "content": prompt}])
        
        if summary:
            # Create a new historical summary entry
            summary_entry = MemoryEntry(
                role="system", 
                content=f"PREVIOUS CONVERSATION SUMMARY: {summary}",
                metadata={"type": "summary"}
            )
            # Reconstruct entries: Summary followed by the recent 10 messages
            self.memory.entries = [summary_entry] + remaining_messages
            self.save()
            return True
            
        return False
