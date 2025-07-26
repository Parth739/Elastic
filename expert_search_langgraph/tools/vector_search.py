import json
from typing import List, Dict, Any
import pandas as pd
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct

class BaseVectorSearchTool:
    def __init__(
        self,
        collection_name: str,
        qdrant_url: str = "http://localhost:6333",
        embedding_model: str = "all-MiniLM-L6-v2",
    ):
        self.model = SentenceTransformer(embedding_model)
        self.client = QdrantClient(url=qdrant_url)
        self.collection_name = collection_name
        self._setup_collection()

    def _setup_collection(self):
        if self.client.collection_exists(self.collection_name):
            self.client.delete_collection(self.collection_name)
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=self.model.get_sentence_embedding_dimension(),
                distance=Distance.COSINE
            ),
        )

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        q_vec = self.model.encode([query])[0].tolist()
        hits = self.client.search(
            collection_name=self.collection_name,
            query_vector=q_vec,
            limit=top_k
        )
        return self._format_results(hits)

    def _format_results(self, hits) -> List[Dict[str, Any]]:
        raise NotImplementedError


class StructuredVectorSearchTool(BaseVectorSearchTool):
    def _aggregate_text(self, doc: dict) -> str:
        parts: List[str] = []
        
        for field in ("bio", "headline"):
            val = doc.get(field, "")
            if isinstance(val, str) and val.strip():
                parts.append(val.strip())

        geo = doc.get("geography_details", [])
        if isinstance(geo, str):
            try:
                geo = json.loads(geo)
            except json.JSONDecodeError:
                geo = []
        if isinstance(geo, list):
            names = [g.get("name","") for g in geo if isinstance(g, dict)]
            if names:
                parts.append(", ".join(names))

        return "\n".join(parts)

    def add_documents(self, docs: pd.DataFrame | List[dict]):
        if isinstance(docs, pd.DataFrame):
            docs = docs.to_dict(orient="records")

        texts = [self._aggregate_text(d) for d in docs]
        embeddings = self.model.encode(texts, show_progress_bar=True)

        points: List[PointStruct] = []
        for d, emb in zip(docs, embeddings):
            rec_id = int(d.get("id", 0))
            points.append(PointStruct(
                id=rec_id,
                vector=emb.tolist(),
                payload=d
            ))
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True
        )

    def _format_results(self, hits) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for h in hits:
            p = h.payload
            results.append({
                "expert_id": int(p.get("id", 0)),
                "expert_name": p.get("expert_name", "") or p.get("name",""),
                "bio": p.get("bio",""),
                "headline": p.get("headline",""),
                "work_summary": "",
                "_score": h.score
            })
        return results


class AgendaVectorSearchTool(BaseVectorSearchTool):
    def add_documents(self, docs: List[dict]):
        texts = [d["text"] for d in docs]
        embs = self.model.encode(texts, show_progress_bar=True)
        points: List[PointStruct] = []
        
        for d, emb in zip(docs, embs):
            payload = {
                "expert_id": d["expert_id"],
                "expert_name": d["expert_name"],
                "bio": d["expert_bio"],
                "headline": d["expert_headline"],
                "work_summary": d["expert_work_summary"],
            }
            points.append(PointStruct(
                id=d["_id"],
                vector=emb.tolist(),
                payload=payload
            ))
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True
        )

    def _format_results(self, hits) -> List[Dict[str, Any]]:
        return [
            {
                "expert_id": h.payload["expert_id"],
                "expert_name": h.payload["expert_name"],
                "bio": h.payload["bio"],
                "headline": h.payload["headline"],
                "work_summary": h.payload["work_summary"],
                "_score": h.score
            }
            for h in hits
        ]
