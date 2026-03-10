from typing import List, Dict, Any, Optional
from datetime import datetime
from src.memory.storage import AgentMemory, MemoryEntry, MemoryLane
from src.utils.logger import logger

class MemoryBroker:
    """
    The control plane for memory exposure in GUIDE.
    Implements the 8-stage retrieval pipeline.
    """
    
    def __init__(self, token_budget: int = 4000):
        self.token_budget = token_budget
        self.weights = {
            "relevance": 0.5,
            "confidence": 0.3,
            "recency": 0.2,
            "sensitivity": 1.0 # Penalty
        }

    def assemble_context_packet(self, request: str, memory: AgentMemory) -> List[Dict[str, str]]:
        """
        The main entry point for the 8-stage pipeline.
        Returns a list of messages ready for LLM input.
        """
        logger.info(f"MemoryBroker: Assembling context for request: '{request[:50]}...'")
        
        # 1. Request Analysis (Simplistic for Phase 1)
        keywords = self._analyze_request(request)
        
        # 2. Lane Selection
        selected_lanes = self._select_lanes(request, memory)
        
        # 3. Retrieval
        candidates = self._retrieve_candidates(selected_lanes, memory)
        
        # 4. Eligibility Filtering (Privacy/Security)
        filtered = self._filter_eligibility(candidates)
        
        # 5. Relevance Ranking
        ranked = self._rank_candidates(request, filtered)
        
        # 6. De-duplication
        unique = self._deduplicate(ranked)
        
        # 7. Retrieval Budget Policy (Trimming)
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

    def _retrieve_candidates(self, lanes: List[str], memory: AgentMemory) -> List[MemoryEntry]:
        candidates = []
        if MemoryLane.SESSION in lanes: candidates.extend(memory.session)
        if MemoryLane.WORKING in lanes: candidates.extend(memory.working)
        if MemoryLane.RESUME in lanes and memory.resume: candidates.append(memory.resume)
        if MemoryLane.SEMANTIC in lanes: candidates.extend(memory.semantic)
        if MemoryLane.EPISODIC in lanes: candidates.extend(memory.episodic)
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

    def _rank_candidates(self, request: str, candidates: List[MemoryEntry]) -> List[MemoryEntry]:
        def calculate_score(entry: MemoryEntry) -> float:
            # Relevance (simplistic keyword match)
            rel = sum(1 for kw in request.lower().split() if kw in entry.content.lower())
            rel_score = min(rel / 5.0, 1.0) # Cap at 1.0
            
            # Recency (higher for more recent)
            now = datetime.utcnow()
            diff = (now - entry.timestamp).total_seconds()
            rec_score = max(0, 1.0 - (diff / 86400)) # Decays over 24h
            
            score = (rel_score * self.weights["relevance"]) + \
                    (entry.confidence * self.weights["confidence"]) + \
                    (rec_score * self.weights["recency"])
            
            return score

        # Sort by calculated score descending
        return sorted(candidates, key=calculate_score, reverse=True)

    def _deduplicate(self, candidates: List[MemoryEntry]) -> List[MemoryEntry]:
        seen = set()
        unique = []
        for c in candidates:
            if c.content not in seen:
                unique.append(c)
                seen.add(c.content)
        return unique

    def _apply_budget(self, candidates: List[MemoryEntry]) -> List[MemoryEntry]:
        # Simplistic budget by count for now, should be token-based
        # Prioritize according to GUIDE Section 7 (Never trim Working or Resume)
        
        working_resume = [c for c in candidates if c.lane in [MemoryLane.WORKING, MemoryLane.RESUME]]
        others = [c for c in candidates if c.lane not in [MemoryLane.WORKING, MemoryLane.RESUME]]
        
        # Max 20 'other' items to stay within context
        return working_resume + others[:20]

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
                "content": f"{prefix}{c.content}"
            })
            
        return packet
