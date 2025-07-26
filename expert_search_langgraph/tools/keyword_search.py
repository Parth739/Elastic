import re
from typing import List, Dict, Any, Optional
import pandas as pd
from rank_bm25 import BM25Okapi

class BaseKeywordSearchTool:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.docs: List[dict] = []
        self.bm25: Optional[BM25Okapi] = None

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"\w+", text.lower())

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if not self.bm25:
            raise RuntimeError("Call add_documents() first")
        tokens = self._tokenize(query)
        scores = self.bm25.get_scores(tokens)
        idxs = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        return self._format_results(idxs, scores)

    def _format_results(self, idxs: List[int], scores: List[float]) -> List[Dict[str, Any]]:
        raise NotImplementedError


class StructuredKeywordSearchTool(BaseKeywordSearchTool):
    def _aggregate_text(self, doc: dict) -> str:
        # Reuse the same logic from vector search
        from .vector_search import StructuredVectorSearchTool
        return StructuredVectorSearchTool(collection_name="temp")._aggregate_text(doc)

    def add_documents(self, docs: pd.DataFrame | List[dict]):
        if isinstance(docs, pd.DataFrame):
            docs = docs.to_dict(orient="records")
        self.docs = docs
        corpus = [self._aggregate_text(d) for d in docs]
        tokenized = [self._tokenize(t) for t in corpus]
        self.bm25 = BM25Okapi(tokenized, k1=self.k1, b=self.b)

    def _format_results(self, idxs: List[int], scores: List[float]) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for i in idxs:
            d = self.docs[i]
            results.append({
                "expert_id": int(d.get("id", 0)),
                "expert_name": d.get("expert_name", "") or d.get("name",""),
                "bio": d.get("bio",""),
                "headline": d.get("headline",""),
                "work_summary": "",
                "_score": float(scores[i])
            })
        return results


class AgendaKeywordSearchTool(BaseKeywordSearchTool):
    def add_documents(self, docs: List[dict]):
        self.docs = docs
        corpus = [d["text"] for d in docs]
        tokenized = [self._tokenize(c) for c in corpus]
        self.bm25 = BM25Okapi(tokenized, k1=self.k1, b=self.b)

    def _format_results(self, idxs: List[int], scores: List[float]) -> List[Dict[str, Any]]:
        return [
            {
                "expert_id": self.docs[i]["expert_id"],
                "expert_name": self.docs[i]["expert_name"],
                "bio": self.docs[i]["expert_bio"],
                "headline": self.docs[i]["expert_headline"],
                "work_summary": self.docs[i]["expert_work_summary"],
                "_score": float(scores[i])
            }
            for i in idxs
        ]
