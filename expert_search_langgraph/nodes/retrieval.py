from typing import Dict, Any
from ..state import ExpertSearchState

def retrieve_experts(
    state: ExpertSearchState,
    normal_vec_tool,
    normal_kw_tool,
    proj_vec_tool,
    proj_kw_tool,
    initial_k: int = 10
) -> Dict[str, Any]:
    """Retrieve experts from all four sources"""
    query = state["query"]
    
    # If we have refined queries, use all of them
    queries = [query]
    if state.get("refined_queries"):
        queries.extend(state["refined_queries"])
    
    # Initialize result lists
    nv_all, nk_all, pv_all, pk_all = [], [], [], []
    
    for q in queries:
        nv_all.extend(normal_vec_tool.search(q, top_k=initial_k))
        nk_all.extend(normal_kw_tool.search(q, top_k=initial_k))
        pv_all.extend(proj_vec_tool.search(q, top_k=initial_k))
        pk_all.extend(proj_kw_tool.search(q, top_k=initial_k))
    
    # Normalize IDs
    for hit in nv_all + nk_all:
        if "id" in hit and "expert_id" not in hit:
            hit["expert_id"] = hit.pop("id")
    
    return {
        "normal_vector_results": nv_all,
        "normal_keyword_results": nk_all,
        "project_vector_results": pv_all,
        "project_keyword_results": pk_all
    }
