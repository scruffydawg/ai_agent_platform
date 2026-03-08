import os
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from src.config import QDRANT_URL, PROJECT_ROOT
from src.utils.logger import logger

class KnowledgeBaseManager:
    """
    Manages the RAG-based Knowledge Base for high-fidelity reference documentation.
    Stored in a dedicated Qdrant collection: 'knowledge_base'
    """
    COLLECTION_NAME = "knowledge_base"

    def __init__(self, url: str = QDRANT_URL):
        self.client = QdrantClient(url=url)
        self._ensure_collection()

    def _ensure_collection(self):
        """Creates the collection if it doesn't exist."""
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.COLLECTION_NAME for c in collections)
            if not exists:
                self.client.create_collection(
                    collection_name=self.COLLECTION_NAME,
                    vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE),
                )
                logger.info(f"Knowledge Base collection '{self.COLLECTION_NAME}' created.")
        except Exception as e:
            logger.error(f"Failed to ensure Knowledge Base collection: {e}")

    async def ingest_document(self, content: str, metadata: Dict[str, Any]):
        """
        Embeds and stores a document chunk in the Knowledge Base.
        Note: Real implementation would chunk the content first.
        """
        try:
            # Placeholder for embedding generation (e.g., via Ollama or OpenAI)
            # In Phase 18, we'll use a simple mock vector if real embeddings aren't wired yet.
            vector = [0.1] * 1536 
            
            point_id = str(os.urandom(16).hex())
            self.client.upsert(
                collection_name=self.COLLECTION_NAME,
                points=[
                    models.PointStruct(
                        id=point_id,
                        vector=vector,
                        payload={
                            "content": content,
                            "metadata": metadata
                        }
                    )
                ]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to ingest document into Knowledge Base: {e}")
            return False

    async def search_reference(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Searches for relevant documentation snippets."""
        try:
            # Placeholder for query embedding
            vector = [0.1] * 1536
            
            results = self.client.search(
                collection_name=self.COLLECTION_NAME,
                query_vector=vector,
                limit=limit
            )
            
            return [hit.payload for hit in results]
        except Exception as e:
            logger.error(f"Knowledge Base search failed: {e}")
            return []

# Global singleton
kb_manager = KnowledgeBaseManager()
