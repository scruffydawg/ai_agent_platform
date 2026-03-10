from typing import List, Dict, Any, Optional
from datetime import datetime
from src.memory.storage import AgentMemory, MemoryEntry, MemoryLane
from src.memory.vector_engine import VectorEngine
from src.llm.client import LLMClient
from src.utils.logger import logger
from apps.api.settings import get_settings

class MemoryBroker:
    """
    The control plane for memory exposure in GUIDE.
    Implements the 8-stage retrieval pipeline.
    """
    
    def __init__(self, token_budget: int = 4000, weights: Optional[Dict[str, float]] = None):
        self.token_budget = token_budget
        self.weights = weights or {
            "relevance": 0.5,
            "confidence": 0.3,
            "recency": 0.2,
            "sensitivity": 1.0 # Penalty
        }
        self.vector_engine = VectorEngine()
        self.llm_client = LLMClient()
        
        # Allow override from global settings
        settings = get_settings()
        if hasattr(settings, 'memory_weights'):
            self.weights.update(settings.memory_weights)

    async def assemble_context_packet(self, request: str, memory: AgentMemory) -> List[Dict[str, str]]:
        """
        The main async entry point for the 8-stage pipeline.
        Returns a list of messages ready for LLM input.
        """
        logger.info(f"MemoryBroker: Assembling context for request: '{request[:50]}...'")
        
        # 1. Request Analysis
        keywords = self._analyze_request(request)
        
        # 2. Lane Selection
        selected_lanes = self._select_lanes(request, memory)
        
        # 3. Retrieval (Postgres + Vector DB)
        # Fetch from lanes PLUS a semantic lookup if applicable
        candidates = await self._retrieve_candidates(selected_lanes, memory, request)
        
        # 4. Eligibility Filtering
        filtered = self._filter_eligibility(candidates)
        
        # 5. Relevance Ranking (Async embedding similarity)
        ranked = await self._rank_candidates(request, filtered)
        
        # 6. De-duplication
        unique = self._deduplicate(ranked)
        
        # 7. Retrieval Budget Policy
        budgeted = self._apply_budget(unique)
        
        # 8. Packet Assembly
        return self._assemble_packet(memory.system_prompt, budgeted)

    def _analyze_request(self, request: str) -> List[str]:
        # Placeholder for more complex NLP/Intent detection
        return request.lower().split()

    def _select_lanes(self, request: str, memory: AgentMemory) -> List[str]:
        # Always include Session and Working
        lanes = [MemoryLane.SESSION, MemoryLane.WORKING]
        
        # Pull Resume if available
        if memory.resume:
            lanes.append(MemoryLane.RESUME)
            
        # Decision logic for Semantic/Episodic
        # If it looks like a question about facts or past work
        if any(kw in request.lower() for kw in ["what", "how", "remember", "previous", "fact", "style"]):
             lanes.append(MemoryLane.SEMANTIC)
             lanes.append(MemoryLane.EPISODIC)
             
        return lanes

    async def _retrieve_candidates(self, lanes: List[str], memory: AgentMemory, request: str) -> List[MemoryEntry]:
        candidates = []
        if MemoryLane.SESSION in lanes: candidates.extend(memory.session)
        if MemoryLane.WORKING in lanes: candidates.extend(memory.working)
        if MemoryLane.RESUME in lanes and memory.resume: candidates.append(memory.resume)
        if MemoryLane.EPISODIC in lanes: candidates.extend(memory.episodic)
        
        # Phase 3: Semantic Retrieval from Vector DB
        if MemoryLane.SEMANTIC in lanes:
            # 1. Start with what's already in the memory object
            candidates.extend(memory.semantic)
            
            # 2. Augment with Qdrant lookup
            try:
                query_vector = await self.llm_client.get_embeddings(request)
                results = await self.vector_engine.search_memory(
                    vector=query_vector,
                    agent_id=memory.agent_id,
                    limit=5
                )
                
                for hit in results:
                    # Avoid duplicates if already in memory object
                    content = hit.payload.get("content") or ""
                    if any(c.content == content for c in candidates):
                        continue
                        
                    candidates.append(MemoryEntry(
                        role=hit.payload.get("role", "assistant"),
                        content=content,
                        lane=MemoryLane.SEMANTIC,
                        source=hit.payload.get("source", "semantic_search"),
                        confidence=hit.score,
                        metadata=hit.payload.get("metadata", {})
                    ))
            except Exception as e:
                logger.error(f"MemoryBroker: Semantic retrieval failed: {e}")
                
        return candidates

    def _filter_eligibility(self, candidates: List[MemoryEntry]) -> List[MemoryEntry]:
        # Block 'confidential' items from default model input
        # This is Phase 1 'Privacy Interceptor' logic
        allowed = []
        for c in candidates:
            if c.sensitivity == "confidential":
                logger.warning(f"MemoryBroker: Filtering out confidential memory: {c.content[:20]}...")
                continue
            allowed.append(c)
        return allowed

    async def _rank_candidates(self, request: str, candidates: List[MemoryEntry]) -> List[MemoryEntry]:
        """Rank candidates using a hybrid of embedding similarity and metadata."""
        if not candidates:
            return []
            
        try:
            # 1. Get query embedding
            query_vector = await self.llm_client.get_embeddings(request)
            
            # 2. Score each candidate
            scored_candidates = []
            for entry in candidates:
                # Get entry embedding
                entry_vector = await self.llm_client.get_embeddings(entry.content)
                
                # Manual dot product
                dot_product = sum(a * b for a, b in zip(query_vector, entry_vector))
                
                # Recency score
                now = datetime.utcnow()
                diff = (now - entry.timestamp).total_seconds()
                rec_score = max(0.0, 1.0 - (diff / 86400.0))
                
                score = (dot_product * self.weights["relevance"]) + \
                        (entry.confidence * self.weights["confidence"]) + \
                        (rec_score * self.weights["recency"])
                
                scored_candidates.append((score, entry))
                
            # 3. Sort by score descending
            scored_candidates.sort(key=lambda x: x[0], reverse=True)
            return [c[1] for c in scored_candidates]
            
        except Exception as e:
            logger.error(f"MemoryBroker: Ranking failed: {e}")
            # Simple keyword fallback
            def fallback_score(entry):
                rel = sum(1 for kw in request.lower().split() if kw in entry.content.lower())
                return rel
            return sorted(candidates, key=fallback_score, reverse=True)

    def _deduplicate(self, candidates: List[MemoryEntry]) -> List[MemoryEntry]:
        seen = set()
        unique = []
        for c in candidates:
            if c.content not in seen:
                unique.append(c)
                seen.add(c.content)
        return unique

    def _apply_budget(self, candidates: List[MemoryEntry]) -> List[MemoryEntry]:
        """
        Implements Section 7 - Retrieval Budget Policy (Overflow Order):
        1. Never trim Working or Resume Memory while active.
        2. Remove duplicate semantic facts first (already handled by _deduplicate).
        3. Trim episodic items next.
        4. Remove lower-confidence semantic items last.
        """
        # Group by lane
        working = [c for c in candidates if c.lane == MemoryLane.WORKING]
        resume = [c for c in candidates if c.lane == MemoryLane.RESUME]
        session = [c for c in candidates if c.lane == MemoryLane.SESSION]
        semantic = [c for c in candidates if c.lane == MemoryLane.SEMANTIC]
        episodic = [c for c in candidates if c.lane == MemoryLane.EPISODIC]

        # Start with untouchables
        selected = working + resume
        
        # Remaining budget (simplistic count-based for now)
        # In a real impl, this would be token-based
        budget = 50 
        budget -= len(selected)

        # Add session (essential for continuity)
        selected += session[:10]
        budget -= 10

        # Add semantic (durable facts), sorted by confidence (highest first)
        semantic_sorted = sorted(semantic, key=lambda x: x.confidence, reverse=True)
        if budget > 0:
            selected += semantic_sorted[:budget]
            budget -= len(semantic_sorted[:budget])

        # Add episodic (past patterns) if budget remains
        if budget > 0:
            selected += episodic[:budget]
            
        return selected

    def _assemble_packet(self, system_prompt: str, candidates: List[MemoryEntry]) -> List[Dict[str, str]]:
        packet = [{"role": "system", "content": system_prompt}]
        
        # Sort back to chronological order for the actual prompt context (optional but usually better for LLMs)
        chronological = sorted(candidates, key=lambda x: x.timestamp)
        
        for c in chronological:
            prefix = ""
            if c.lane == MemoryLane.WORKING: prefix = "[WORKING]: "
            elif c.lane == MemoryLane.RESUME: prefix = "[RESUME]: "
            elif c.lane == MemoryLane.SEMANTIC: prefix = "[KNOWLEDGE]: "
            elif c.lane == MemoryLane.EPISODIC: prefix = "[PAST EPISODE]: "
            
            packet.append({
                "role": c.role,
                "content": f"{prefix}{c.content}",
                "lane": c.lane,
                "confidence": c.confidence,
                "provenance": c.provenance,
                "metadata": c.metadata
            })
            
        # Add Trace Metadata as a hidden system message or metadata field
        # For now, we'll append a summary of the retrieval trace
        packet.append({
            "role": "system",
            "content": f"[TRACE]: Context assembled from {len(candidates)} items. Model: v5.0. Budget: {self.token_budget} tokens."
        })
            
        return packet
