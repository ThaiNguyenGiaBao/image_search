from typing import Any, Dict, List, Optional, Sequence, Union

from qdrant_client import QdrantClient,models
from qdrant_client.http.models import (
    Distance,
    VectorParams,
    ScalarQuantization,
    ScalarQuantizationConfig
)
from qdrant_client.models import PointStruct, ScoredPoint
import os
from dotenv import load_dotenv
load_dotenv()


class Qdrant:
    def __init__(self, collection_name: str, dim: int = 768):
        self.client = QdrantClient(
            url=os.getenv("QDRANT_URI", "https://localhost:6333"),  
            api_key=os.getenv("QDRANT_API_KEY", ""),
            timeout=120)
        self.collection_name = collection_name
        self.dim = dim

    def ensure_collection(self):
        cols = self.client.get_collections().collections
        names = [c.name for c in cols]
        if self.collection_name not in names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.dim, distance=Distance.COSINE, on_disk=True),
                quantization_config=models.ScalarQuantization(
                    scalar=models.ScalarQuantizationConfig(
                        type=models.ScalarType.INT8,
                        quantile=0.99,
                        always_ram=True,
                    ),
                ),
            )

    def upsert_points(self, points: List[PointStruct]):
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
    def upsert_vector(self, id: int, vector: List[float], payload: Optional[Dict[str, Any]] = None):
        point = PointStruct(
            id=id,
            vector=vector,
            payload=payload or {}
        )
        self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )
        
    def upsert_vectors(self, vectors: Sequence[List[float]], payloads: Optional[Sequence[Dict[str, Any]]] = None):
        points = [
            PointStruct(
                id=idx,
                vector=vector,
                payload=payload or {}
            )
            for idx, (vector, payload) in enumerate(zip(vectors, payloads or [{}] * len(vectors)))
        ]
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
    def query_points(self, query_vector: List[float], limit: int = 10) -> List[ScoredPoint]:
        return self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=limit,
            search_params=models.SearchParams(
                quantization=models.QuantizationSearchParams(rescore=True, oversampling=2)
            )
        )
