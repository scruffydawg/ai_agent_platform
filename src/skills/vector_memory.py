from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
from src.config import QDRANT_URL
from src.utils.logger import logger

class VectorMemory:
    def __init__(self, collection_name="agent_memory"):
        self.client = QdrantClient(url=QDRANT_URL)
        self.collection_name = collection_name
        # Local-First Embedding Model (all-MiniLM-L6-v2)
        # Size: 384, very fast, high precision for retrieval
        try:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            logger.error(f"Failed to load sentence-transformer: {e}")
            self.model = None
            
        self._ensure_collection()

    def _ensure_collection(self):
        try:
            collections = self.client.get_collections().collections
            if not any(c.name == self.collection_name for c in collections):
                # Using size 384 for all-MiniLM-L6-v2
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE),
                )
                logger.info(f"Created collection: {self.collection_name} with size 384")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")

    def embed(self, text: str):
        """Generate local embedding for a string."""
        if not self.model:
            return None
        return self.model.encode(text).tolist()

    def upsert(self, ids, texts, payloads=None):
        """Standardized upsert with auto-embedding."""
        if not self.model:
             logger.error("Cannot upsert: Embedding model not loaded.")
             return

        vectors = [self.embed(t) for t in texts]
        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=models.Batch(
                    ids=ids,
                    vectors=vectors,
                    payloads=payloads
                )
            )
        except Exception as e:
            logger.error(f"Qdrant Upsert Error: {e}")

    def search(self, query: str, limit=5):
        """Search based on query text."""
        if not self.model:
            return []
            
        vector = self.embed(query)
        try:
            return self.client.search(
                collection_name=self.collection_name,
                query_vector=vector,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Qdrant Search Error: {e}")
            return []

vector_memory = VectorMemory()
