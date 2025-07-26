from typing import List, Dict, Any

class AgendaResultsReranker:
    def __init__(self, alpha: float = 0.5):
        self.alpha = alpha

    def _get_eid(self, hit: Dict[str, Any]) -> int:
        if "expert_id" in hit:
            return hit["expert_id"]
        if "id" in hit:
            return hit["id"]
        raise KeyError(f"No 'expert_id' or 'id' in hit: {hit}")

    def rerank_simple(
        self,
        vec_hits: List[Dict[str, Any]],
        kw_hits: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        merged: Dict[int, Dict[str, Any]] = {}

        for hit in vec_hits:
            eid = self._get_eid(hit)
            rec = merged.setdefault(eid, {
                **hit,
                "vec_score": hit.get("_score", 0.0),
                "kw_score": 0.0
            })
            rec["vec_score"] = max(rec["vec_score"], hit.get("_score", 0.0))

        for hit in kw_hits:
            eid = self._get_eid(hit)
            rec = merged.setdefault(eid, {
                **hit,
                "vec_score": 0.0,
                "kw_score": hit.get("_score", 0.0)
            })
            rec["kw_score"] = max(rec["kw_score"], hit.get("_score", 0.0))

        records = list(merged.values())
        if not records:
            return []

        max_vec = max(r["vec_score"] for r in records) or 1.0
        max_kw = max(r["kw_score"] for r in records) or 1.0

        for r in records:
            r["vec_norm"] = r["vec_score"] / max_vec
            r["kw_norm"] = r["kw_score"] / max_kw
            r["fused_score"] = (
                self.alpha * r["vec_norm"] +
                (1 - self.alpha) * r["kw_norm"]
            )

        records.sort(key=lambda r: r["fused_score"], reverse=True)
        return records[:top_k]
