from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from .state import ExpertSearchState
from .nodes.retrieval import retrieve_experts
from .nodes.reranking import rerank_results
from .nodes.refinement import check_and_refine
from functools import partial

def create_expert_search_graph(
    normal_vec_tool,
    normal_kw_tool,
    proj_vec_tool,
    proj_kw_tool,
    reranker,
    refiner=None,
    initial_k=10,
    final_n=5,
    quality_threshold=0.5
):
    """Create the expert search LangGraph"""
    
    # Create the graph
    workflow = StateGraph(ExpertSearchState)
    
    # Create node functions with tools bound
    retrieve_fn = partial(
        retrieve_experts,
        normal_vec_tool=normal_vec_tool,
        normal_kw_tool=normal_kw_tool,
        proj_vec_tool=proj_vec_tool,
        proj_kw_tool=proj_kw_tool,
        initial_k=initial_k
    )
    
    rerank_fn = partial(
        rerank_results,
        reranker=reranker,
        initial_k=initial_k
    )
    
    refine_fn = partial(
        check_and_refine,
        refiner=refiner,
        quality_threshold=quality_threshold
    )
    
    def select_final_results(state: ExpertSearchState) -> Dict[str, Any]:
        """Select final top N results"""
        return {
            "final_results": state["merged_results"][:final_n]
        }
    
    # Add nodes
    workflow.add_node("retrieve", retrieve_fn)
    workflow.add_node("rerank", rerank_fn)
    workflow.add_node("check_refine", refine_fn)
    workflow.add_node("select_final", select_final_results)
    
    # Define edges
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "rerank")
    workflow.add_edge("rerank", "check_refine")
    
    # Conditional edge: refine if quality is low
    def should_refine_route(state: ExpertSearchState):
        return "retrieve" if state["should_refine"] else "select_final"
    
    workflow.add_conditional_edges(
        "check_refine",
        should_refine_route,
        {
            "retrieve": "retrieve",
            "select_final": "select_final"
        }
    )
    
    workflow.add_edge("select_final", END)
    
    return workflow.compile()
