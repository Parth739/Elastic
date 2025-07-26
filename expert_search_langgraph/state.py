from typing import List, Dict, Any, Optional, TypedDict
from langgraph.graph import MessagesState

class ExpertSearchState(TypedDict):
    """State for the expert search graph"""
    query: str
    refined_queries: List[str]
    normal_vector_results: List[Dict[str, Any]]
    normal_keyword_results: List[Dict[str, Any]]
    project_vector_results: List[Dict[str, Any]]
    project_keyword_results: List[Dict[str, Any]]
    merged_results: List[Dict[str, Any]]
    final_results: List[Dict[str, Any]]
    quality_score: float
    should_refine: bool
    iteration: int
