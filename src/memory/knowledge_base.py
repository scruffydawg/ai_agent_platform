from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from src.config import QDRANT_URL, PROJECT_ROOT
from src.utils.logger import logger
import uuid

class KnowledgeBaseManager:
    """
    Manages the RAG-based Knowledge Base for high-fidelity reference documentation.
    Stored in a dedicated Qdrant collection: 'knowledge_base'
    """
    COLLECTION_NAME = "knowledge_base"

    def __init__(self, url: str = QDRANT_URL):
        self._client = None
        self._model = None
        self._url = url
        self._collection_ensured = False
        # Default vector size for all-MiniLM-L6-v2
        self.vector_size = 384

    @property
    def client(self):
        if self._client is None:
            self._client = QdrantClient(url=self._url)
        return self._client

    @property
    def model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception as e:
                logger.error(f"KB: Failed to load sentence-transformer: {e}")
                self._model = None
        return self._model

    def _ensure_collection(self):
        if self._collection_ensured:
            return
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.COLLECTION_NAME for c in collections)
            
            if exists:
                # Check current configuration
                config = self.client.get_collection(self.COLLECTION_NAME).config
                current_size = config.params.vectors.size
                if current_size != self.vector_size:
                    logger.warning(f"Dimension mismatch in {self.COLLECTION_NAME} (found {current_size}, need {self.vector_size}). Re-creating...")
                    self.client.delete_collection(self.COLLECTION_NAME)
                    exists = False

            if not exists:
                self.client.create_collection(
                    collection_name=self.COLLECTION_NAME,
                    vectors_config=models.VectorParams(size=self.vector_size, distance=models.Distance.COSINE),
                )
                logger.info(f"Knowledge Base collection '{self.COLLECTION_NAME}' created with size {self.vector_size}.")
            self._collection_ensured = True
        except Exception as e:
            logger.error(f"Failed to ensure Knowledge Base collection: {e}")

    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Simple recursive-style chunking with overlap."""
        chunks = []
        if len(text) <= chunk_size:
            return [text]
        
        start = 0
        while start < len(text):
            end = int(start + chunk_size)
            chunk = text[int(start):end]
            chunks.append(chunk)
            start = int(start + (chunk_size - overlap))
        return chunks

    async def ingest_document(self, content: str, metadata: Dict[str, Any]):
        """
        Chunks, embeds, and stores a document in the Knowledge Base.
        """
        self._ensure_collection()
        if not self.model:
            logger.error("KB Ingestion failed: Embedding model not loaded.")
            return False

        try:
            chunks = self.chunk_text(content)
            points = []
            
            for i, chunk in enumerate(chunks):
                # Generate real embedding
                vector = self.model.encode(chunk).tolist()
                point_id = str(uuid.uuid4())
                
                points.append(models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "content": chunk,
                        "metadata": {
                            **metadata,
                            "chunk_index": i,
                            "total_chunks": len(chunks)
                        }
                    }
                ))
            
            self.client.upsert(
                collection_name=self.COLLECTION_NAME,
                points=points
            )
            logger.info(f"Ingested document '{metadata.get('filename', 'unknown')}' into KB ({len(chunks)} chunks).")
            return True
        except Exception as e:
            logger.error(f"Failed to ingest document into Knowledge Base: {e}")
            return False

    async def search_reference(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Searches for relevant documentation snippets using vector search."""
        self._ensure_collection()
        if not self.model:
            logger.error("KB Search failed: Embedding model not loaded.")
            return []

        try:
            # Generate query embedding
            vector = self.model.encode(query).tolist()
            
            results = self.client.search(
                collection_name=self.COLLECTION_NAME,
                query_vector=vector,
                limit=limit,
                with_payload=True
            )
            
            return [hit.payload for hit in results]
        except Exception as e:
            logger.error(f"Knowledge Base search failed: {e}")
            return []

# Global singleton
kb_manager = KnowledgeBaseManager()
