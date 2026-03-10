"""
SkillIndexer — embeds skill metadata into Qdrant `skill_registry` collection.
Each skill produces multiple chunks: summary, per-method, docs_links.
Agents can search this collection to discover the right skill for any task.
"""
import hashlib
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from src.config import QDRANT_URL
from src.utils.logger import logger

COLLECTION_NAME = "skill_registry"
VECTOR_SIZE = 384  # all-MiniLM-L6-v2


class SkillIndexer:
    """
    Indexes skill definitions into Qdrant for semantic retrieval by the agent swarm.
    Uses the same embedding model as VectorMemory (all-MiniLM-L6-v2, local, no API cost).
    """

    def __init__(self):
        self._client = None
        self._model = None

    @property
    def client(self):
        if self._client is None:
            self._client = QdrantClient(url=QDRANT_URL)
        return self._client

    @property
    def model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception as e:
                logger.error(f"SkillIndexer: Failed to load embedding model: {e}")
                self._model = None
        return self._model

    def _ensure_collection(self):
        try:
            existing = [c.name for c in self.client.get_collections().collections]
            if COLLECTION_NAME not in existing:
                self.client.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=models.VectorParams(
                        size=VECTOR_SIZE, distance=models.Distance.COSINE
                    ),
                )
                logger.info(f"SkillIndexer: Created collection '{COLLECTION_NAME}'")
        except Exception as e:
            logger.error(f"SkillIndexer: Qdrant connection failed: {e}")

    def _embed(self, text: str) -> Optional[List[float]]:
        if not self.model or not text.strip():
            return None
        return self.model.encode(text).tolist()

    def _stable_id(self, text: str) -> int:
        """Deterministic integer ID from string — allows idempotent upserts."""
        return int(hashlib.md5(text.encode()).hexdigest(), 16) % (10 ** 12)

    def index(self, skill: Dict[str, Any]) -> bool:
        """
        Index a skill into Qdrant. Creates multiple chunks per skill.

        Args:
            skill: dict with keys: name, description, subtype, filename,
                   methods (list of {name, doc, params, returns}),
                   docs_links (list of {label, url}),
                   sample_calls (list of {action, endpoint, notes})
        Returns:
            True on success.
        """
        # Trigger creation/check on first index
        self._ensure_collection()

        if not self.model:
            logger.error("SkillIndexer: Cannot index — embedding model not loaded.")
            return False

        name = skill.get("name", "Unknown")
        subtype = skill.get("subtype", "skill")
        filename = skill.get("filename", "")
        chunks = []

        # ── Chunk 1: Capability summary ────────────────────────────────────────
        summary = skill.get("description", "")
        if summary:
            chunks.append({
                "text": f"{name}: {summary}",
                "chunk_type": "summary",
                "name": name,
                "subtype": subtype,
                "filename": filename,
            })

        # ── Chunk 2+: Per-method ───────────────────────────────────────────────
        for method in skill.get("methods", []):
            m_name = method.get("name", "")
            m_doc = method.get("doc", "")
            m_params = ", ".join(method.get("params", []))
            text = f"{name}.{m_name}({m_params}): {m_doc}"
            chunks.append({
                "text": text,
                "chunk_type": "method",
                "name": name,
                "subtype": subtype,
                "filename": filename,
                "method": m_name,
            })

        # ── Chunk 3+: Docs links (descriptions) ───────────────────────────────
        for link in skill.get("docs_links", []):
            label = link.get("label", "")
            url = link.get("url", "")
            text = f"{name} reference: {label} ({url})"
            chunks.append({
                "text": text,
                "chunk_type": "docs_link",
                "name": name,
                "subtype": subtype,
                "filename": filename,
                "url": url,
            })

        if not chunks:
            logger.warning(f"SkillIndexer: No chunks generated for '{name}'")
            return False

        # ── Upsert all chunks ──────────────────────────────────────────────────
        try:
            points = []
            for chunk in chunks:
                vector = self._embed(chunk["text"])
                if vector is None:
                    continue
                point_id = self._stable_id(chunk["text"])
                points.append(models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=chunk,
                ))

            self.client.upsert(collection_name=COLLECTION_NAME, points=points)
            logger.info(f"SkillIndexer: Indexed '{name}' — {len(points)} chunks")
            return True
        except Exception as e:
            logger.error(f"SkillIndexer: Upsert failed for '{name}': {e}")
            return False

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Semantic search across all indexed skills.

        Args:
            query: natural language query (e.g. 'generate a PowerPoint slide')
            limit: max results
        Returns:
            List of payloads from matching chunks.
        """
        vector = self._embed(query)
        if not vector:
            return []
        try:
            results = self.client.search(
                collection_name=COLLECTION_NAME,
                query_vector=vector,
                limit=limit,
            )
            return [r.payload for r in results]
        except Exception as e:
            logger.error(f"SkillIndexer: Search failed: {e}")
            return []

    def delete(self, skill_name: str):
        """Remove all chunks for a given skill name."""
        try:
            self.client.delete(
                collection_name=COLLECTION_NAME,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[models.FieldCondition(
                            key="name",
                            match=models.MatchValue(value=skill_name)
                        )]
                    )
                )
            )
            logger.info(f"SkillIndexer: Deleted all chunks for '{skill_name}'")
        except Exception as e:
            logger.error(f"SkillIndexer: Delete failed for '{skill_name}': {e}")


skill_indexer = SkillIndexer()
