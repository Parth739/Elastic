from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Any, Dict
from models.schemas import SearchQuery, Expert, QueryType, ReasoningTrace
from agents.query_analyzer import QueryAnalyzer
from agents.search_agent import SearchAgent
from agents.reranker import Reranker
import asyncio
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class WorkflowState(TypedDict):
    query: str
    search_query: SearchQuery
    experts: List[Expert]
    final_experts: List[Expert]
    metadata: Dict[str, Any]
    reasoning_traces: List[ReasoningTrace]

class ExpertSearchWorkflow:
    """Original workflow for basic expert search with limited retries"""
    def __init__(self):
        self.query_analyzer = QueryAnalyzer()
        self.search_agent = SearchAgent()
        self.reranker = Reranker()
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        workflow = StateGraph(WorkflowState)
        
        # Add nodes
        workflow.add_node("analyze_query", self._analyze_query)
        workflow.add_node("search_experts", self._search_experts)
        workflow.add_node("rerank_results", self._rerank_results)
        workflow.add_node("quality_check", self._quality_check)
        
        # Add edges
        workflow.add_edge("analyze_query", "search_experts")
        workflow.add_edge("search_experts", "rerank_results")
        workflow.add_edge("rerank_results", "quality_check")
        
        # Conditional edge from quality check
        workflow.add_conditional_edges(
            "quality_check",
            self._should_retry,
            {
                "retry": "search_experts",
                "end": END
            }
        )
        
        # Set entry point
        workflow.set_entry_point("analyze_query")
        
        return workflow.compile()
    
    def _add_reasoning_trace(self, state: WorkflowState, step: str, reasoning: str, decision: str = None):
        """Helper to add reasoning traces"""
        trace = ReasoningTrace(
            step=step,
            reasoning=reasoning,
            decision=decision,
            timestamp=datetime.now().isoformat()
        )
        if "reasoning_traces" not in state:
            state["reasoning_traces"] = []
        state["reasoning_traces"].append(trace)
    
    async def _analyze_query(self, state: WorkflowState) -> WorkflowState:
        """Analyze the input query"""
        try:
            # Try with reasoning first
            search_query, reasoning_traces = await self.query_analyzer.analyze_with_reasoning(state["query"])
            
            state["search_query"] = search_query
            state["metadata"]["query_type"] = search_query.query_type.value
            
            # Add reasoning traces
            for trace in reasoning_traces:
                self._add_reasoning_trace(state, trace.step, trace.reasoning, trace.decision)
                
        except Exception as e:
            logger.error(f"Error in query analysis with reasoning: {e}")
            # Fallback to basic analysis
            search_query = await self.query_analyzer.analyze(state["query"])
            state["search_query"] = search_query
            state["metadata"]["query_type"] = search_query.query_type.value
            
            self._add_reasoning_trace(
                state, 
                "Query Analysis", 
                "Used fallback analysis due to error",
                search_query.query_type.value
            )
        
        return state
    
    async def _search_experts(self, state: WorkflowState) -> WorkflowState:
        """Search for experts based on query type"""
        search_query = state["search_query"]
        
        try:
            # Add search strategy reasoning
            if search_query.query_type == QueryType.DIRECT_EXPERT:
                strategy_reasoning = "Using direct expert search strategy because the query is looking for specific expert characteristics"
            else:
                strategy_reasoning = "Using project-based search strategy because the query mentions project/implementation needs"
            
            self._add_reasoning_trace(state, "Search Strategy", strategy_reasoning, search_query.query_type.value)
            
            # Perform search with reasoning
            experts, search_reasoning = await self.search_agent.search_with_reasoning(search_query)
            
            state["experts"] = experts
            state["metadata"]["search_count"] = len(experts)
            
            # Add search reasoning
            self._add_reasoning_trace(state, "Search Execution", search_reasoning, f"Found {len(experts)} experts")
            
        except Exception as e:
            logger.error(f"Error in search with reasoning: {e}")
            # Fallback to basic search
            if search_query.query_type == QueryType.DIRECT_EXPERT:
                experts = await self.search_agent.search_direct_experts(search_query)
            else:
                experts = await self.search_agent.search_project_based_experts(search_query)
            
            state["experts"] = experts
            state["metadata"]["search_count"] = len(experts)
            
            self._add_reasoning_trace(
                state, 
                "Search Execution", 
                "Used fallback search method",
                f"Found {len(experts)} experts"
            )
        
        return state
    
    async def _rerank_results(self, state: WorkflowState) -> WorkflowState:
        """Rerank the search results"""
        try:
            # Try reranking with reasoning
            reranked_experts, rerank_reasoning = await self.reranker.rerank_with_reasoning(
                state["experts"],
                state["search_query"]
            )
            
            state["final_experts"] = reranked_experts[:10]  # Top 10 results
            
            # Add reranking reasoning
            self._add_reasoning_trace(
                state, 
                "Result Reranking", 
                rerank_reasoning,
                f"Reranked to top {len(state['final_experts'])} experts"
            )
            
        except Exception as e:
            logger.error(f"Error in reranking with reasoning: {e}")
            # Fallback to basic reranking
            reranked_experts = await self.reranker.rerank_experts(
                state["experts"],
                state["search_query"]
            )
            state["final_experts"] = reranked_experts[:10]
            
            self._add_reasoning_trace(
                state,
                "Result Reranking",
                "Used fallback reranking method",
                f"Reranked to top {len(state['final_experts'])} experts"
            )
        
        return state
    
    async def _quality_check(self, state: WorkflowState) -> WorkflowState:
        """Check if results meet quality threshold"""
        experts = state["final_experts"]
        
        # Simple quality check - ensure we have results
        quality_checks = {
            "has_results": len(experts) > 0,
            "minimum_count": len(experts) >= 3,
            "has_high_scores": any(e.score > 1.0 for e in experts) if experts else False
        }
        
        quality_score = sum(quality_checks.values()) / len(quality_checks)
        
        state["metadata"]["quality_score"] = quality_score > 0.5
        state["metadata"]["retry_count"] = state["metadata"].get("retry_count", 0)
        
        # Build quality reasoning
        quality_reasoning = []
        if quality_checks["has_results"]:
            quality_reasoning.append(f"Found {len(experts)} experts")
        else:
            quality_reasoning.append("No experts found")
            
        if quality_checks["minimum_count"]:
            quality_reasoning.append("Sufficient number of results")
        else:
            quality_reasoning.append("Too few results")
            
        if quality_checks["has_high_scores"]:
            quality_reasoning.append("Contains highly relevant matches")
        else:
            quality_reasoning.append("Low relevance scores")
        
        self._add_reasoning_trace(
            state,
            "Quality Assessment",
            " | ".join(quality_reasoning),
            "Pass" if state["metadata"]["quality_score"] else "Retry needed"
        )
        
        return state
    
    def _should_retry(self, state: WorkflowState) -> str:
        """Determine if we should retry the search"""
        quality_score = state["metadata"].get("quality_score", False)
        retry_count = state["metadata"].get("retry_count", 0)
        
        if not quality_score and retry_count < 2:
            state["metadata"]["retry_count"] = retry_count + 1
            self._add_reasoning_trace(
                state,
                "Retry Decision",
                f"Quality check failed, retrying (attempt {retry_count + 1}/2)",
                "retry"
            )
            return "retry"
        
        self._add_reasoning_trace(
            state,
            "Workflow Complete",
            "Ending workflow - either quality passed or max retries reached",
            "end"
        )
        return "end"
    
    async def run(self, query: str) -> Dict[str, Any]:
        """Run the workflow"""
        initial_state = {
            "query": query,
            "search_query": None,
            "experts": [],
            "final_experts": [],
            "metadata": {},
            "reasoning_traces": []
        }
        
        try:
            result = await self.workflow.ainvoke(initial_state)
            
            return {
                "experts": result["final_experts"],
                "metadata": result["metadata"],
                "reasoning_traces": result.get("reasoning_traces", [])
            }
            
        except Exception as e:
            logger.error(f"Workflow execution error: {e}")
            return {
                "experts": [],
                "metadata": {"error": str(e)},
                "reasoning_traces": initial_state.get("reasoning_traces", [])
            }
