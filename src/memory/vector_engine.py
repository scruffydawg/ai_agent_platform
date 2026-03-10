from qdrant_client import QdrantClient, AsyncQdrantClient
from qdrant_client.http import models
from apps.api.settings import get_settings
from typing import List, Dict, Any, Optional
import uuid

class VectorEngine:
    def __init__(self):
        self.settings = get_settings()
        self.client = AsyncQdrantClient(url=self.settings.qdrant_url)
        self.collection_name = "guide_memory"

    async def init_collections(self):
        collections = await self.client.get_collections()
        exists = any(c.name == self.collection_name for c in collections.collections)
        
        if not exists:
            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE),
            )

    async def upsert_memory(self, entry_id: str, vector: List[float], metadata: Dict[str, Any], modality: str = "text"):
        """Upsert memory with modality tracking (Phase 7)."""
        metadata["modality"] = modality
        await self.client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=entry_id,
                    vector=vector,
                    payload=metadata
                )
            ]
        )

    async def search_memory(self, vector: List[float], agent_id: str, limit: int = 5, filter_dict: Optional[Dict[str, Any]] = None, modality: Optional[str] = None):
        """Semantic search with optional modality filter."""
        must = [models.FieldCondition(key="agent_id", match=models.MatchValue(value=agent_id))]
        if modality:
            must.append(models.FieldCondition(key="modality", match=models.MatchValue(value=modality)))
        if filter_dict:
            for k, v in filter_dict.items():
                must.append(models.FieldCondition(key=k, match=models.MatchValue(value=v)))
        
        search_filter = models.Filter(must=must)

        return await self.client.search(
            collection_name=self.collection_name,
            query_vector=vector,
            limit=limit,
            query_filter=search_filter
        )

    async def delete_agent_points(self, agent_id: str):
        """Wipes all points for a specific agent."""
        await self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[models.FieldCondition(key="agent_id", match=models.MatchValue(value=agent_id))]
                )
            )
        )
