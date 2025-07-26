from typing import Dict, Any
from ..state import ExpertSearchState
from ..tools.reranker import AgendaResultsReranker

def rerank_results(
    state: ExpertSearchState,
    reranker: AgendaResultsReranker,
    initial_k: int = 10
) -> Dict[str, Any]:
    """Merge and rerank all results"""
    vec_hits = state["normal_vector_results"] + state["project_vector_results"]
    kw_hits = state["normal_keyword_results"] + state["project_keyword_results"]
    
    merged = reranker.rerank_simple(vec_hits, kw_hits, top_k=initial_k)
    
    # Calculate quality score
    quality_score = merged[0]["fused_score"] if merged else 0.0
    
    return {
        "merged_results": merged,
        "quality_score": quality_score
    }
