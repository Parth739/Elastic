from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Any, Dict, Optional
from models.schemas import SearchQuery, Expert, QueryType, ReasoningTrace, AgentState, SearchResult
from agents.query_analyzer import QueryAnalyzer
from agents.search_agent import SearchAgent
from agents.reranker import Reranker
from agents.learning_agent import LearningAgent
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)

class AutonomousWorkflowState(TypedDict):
    query: str
    search_query: SearchQuery
    experts: List[Expert]
    final_experts: List[Expert]
    metadata: Dict[str, Any]
    reasoning_traces: List[ReasoningTrace]
    quality_score: float
    iteration: int
    strategies_tried: List[str]
    agent_state: AgentState
    suggestions: List[str]
    alternative_queries: List[str]

class AutonomousExpertSearchWorkflow:
    def __init__(self):
        self.query_analyzer = QueryAnalyzer()
        self.search_agent = SearchAgent()
        self.reranker = Reranker()
        self.learning_agent = LearningAgent()
        self.workflow = self._create_workflow()
        self.max_iterations = 10
        self.target_quality = 0.8
    
    def _create_workflow(self) -> StateGraph:
        workflow = StateGraph(AutonomousWorkflowState)
        
        # Add nodes
        workflow.add_node("initialize", self._initialize)
        workflow.add_node("select_strategy", self._select_strategy)
        workflow.add_node("analyze_query", self._analyze_query)
        workflow.add_node("search_experts", self._search_experts)
        workflow.add_node("rerank_results", self._rerank_results)
        workflow.add_node("evaluate_quality", self._evaluate_quality)
        workflow.add_node("generate_suggestions", self._generate_suggestions)
        workflow.add_node("learn_from_results", self._learn_from_results)
        workflow.add_node("decide_next_action", self._decide_next_action)
        
        # Add edges
        workflow.add_edge("initialize", "select_strategy")
        workflow.add_edge("select_strategy", "analyze_query")
        workflow.add_edge("analyze_query", "search_experts")
        workflow.add_edge("search_experts", "rerank_results")
        workflow.add_edge("rerank_results", "evaluate_quality")
        workflow.add_edge("evaluate_quality", "generate_suggestions")
        workflow.add_edge("generate_suggestions", "learn_from_results")
        workflow.add_edge("learn_from_results", "decide_next_action")
        
        # Conditional edges
        workflow.add_conditional_edges(
            "decide_next_action",
            self._should_continue,
            {
                "continue": "select_strategy",
                "complete": END
            }
        )
        
        workflow.set_entry_point("initialize")
        
        return workflow.compile()
    
    async def _initialize(self, state: AutonomousWorkflowState) -> AutonomousWorkflowState:
        """Initialize the autonomous workflow"""
        state["iteration"] = 0
        state["strategies_tried"] = []
        state["agent_state"] = AgentState.SEARCHING
        state["reasoning_traces"] = []
        state["suggestions"] = []
        state["alternative_queries"] = []
        
        self._add_reasoning_trace(
            state,
            "Workflow Initialization",
            f"Starting autonomous search for: {state['query']}",
            "initialized"
        )
        
        return state
    
    async def _select_strategy(self, state: AutonomousWorkflowState) -> AutonomousWorkflowState:
        """Select search strategy based on learning"""
        strategy, confidence = await self.learning_agent.select_strategy(
            state["query"],
            state["strategies_tried"]
        )
        
        state["metadata"]["current_strategy"] = strategy
        state["metadata"]["strategy_confidence"] = confidence
        state["strategies_tried"].append(strategy)
        
        self._add_reasoning_trace(
            state,
            "Strategy Selection",
            f"Selected {strategy} strategy with {confidence:.2f} confidence based on historical performance",
            strategy
        )
        
        return state
    
    async def _analyze_query(self, state: AutonomousWorkflowState) -> AutonomousWorkflowState:
        """Analyze query with selected strategy"""
        strategy = state["metadata"]["current_strategy"]
        
        # Map strategy to query type
        strategy_to_type = {
            "direct_expert": QueryType.DIRECT_EXPERT,
            "project_based": QueryType.PROJECT_BASED,
            "skill_decomposition": QueryType.SKILL_DECOMPOSITION,
            "network_expansion": QueryType.NETWORK_EXPANSION,
            "semantic_similarity": QueryType.SEMANTIC_SIMILARITY
        }
        
        # Force specific query type based on strategy
        search_query, reasoning_traces = await self.query_analyzer.analyze_with_reasoning(
            state["query"]
        )
        
        search_query.query_type = strategy_to_type.get(strategy, QueryType.DIRECT_EXPERT)
        search_query.target_quality = self.target_quality
        
        state["search_query"] = search_query
        
        for trace in reasoning_traces:
            self._add_reasoning_trace(state, trace.step, trace.reasoning, trace.decision)
        
        return state
    
    async def _search_experts(self, state: AutonomousWorkflowState) -> AutonomousWorkflowState:
        """Execute search with selected strategy"""
        search_query = state["search_query"]
        strategy = state["metadata"]["current_strategy"]
        
        # Execute different search strategies
        if strategy == "skill_decomposition":
            experts = await self._skill_decomposition_search(search_query)
        elif strategy == "network_expansion":
            experts = await self._network_expansion_search(search_query)
        elif strategy == "semantic_similarity":
            experts = await self._semantic_similarity_search(search_query)
        else:
            experts, reasoning = await self.search_agent.search_with_reasoning(search_query)
            self._add_reasoning_trace(state, "Search Execution", reasoning, f"Found {len(experts)} experts")
        
        state["experts"] = experts
        state["metadata"]["search_count"] = len(experts)
        
        return state
    
    async def _skill_decomposition_search(self, search_query: SearchQuery) -> List[Expert]:
        """Break down query into skills and search separately"""
        all_experts = []
        
        # Decompose into individual skills
        skills = search_query.keywords[:5]
        
        for skill in skills:
            skill_query = SearchQuery(
                original_query=f"expert in {skill}",
                query_type=QueryType.DIRECT_EXPERT,
                enhanced_queries=[],
                keywords=[skill]
            )
            
            experts = await self.search_agent.search_direct_experts(skill_query)
            all_experts.extend(experts[:3])  # Top 3 per skill
        
        # Deduplicate
        unique_experts = {e.id: e for e in all_experts}
        return list(unique_experts.values())
    
    async def _network_expansion_search(self, search_query: SearchQuery) -> List[Expert]:
        """Search and then expand through similar experts"""
        # Initial search
        initial_experts = await self.search_agent.search_direct_experts(search_query)
        
        if not initial_experts:
            return []
        
        # Find similar experts based on functions/skills
        expanded_experts = []
        for expert in initial_experts[:3]:
            if expert.functions:
                for function in expert.functions[:2]:
                    similar_query = SearchQuery(
                        original_query=f"expert in {function}",
                        query_type=QueryType.DIRECT_EXPERT,
                        enhanced_queries=[],
                        keywords=[function]
                    )
                    similar = await self.search_agent.search_direct_experts(similar_query)
                    expanded_experts.extend(similar[:2])
        
        # Combine and deduplicate
        all_experts = initial_experts + expanded_experts
        unique_experts = {e.id: e for e in all_experts}
        return list(unique_experts.values())
    
    async def _semantic_similarity_search(self, search_query: SearchQuery) -> List[Expert]:
        """Use pure semantic search with embeddings"""
        # Focus on semantic search only
        return await self.search_agent.search_direct_experts(search_query)
    
    async def _rerank_results(self, state: AutonomousWorkflowState) -> AutonomousWorkflowState:
        """Rerank with reasoning"""
        experts, reasoning = await self.reranker.rerank_with_reasoning(
            state["experts"],
            state["search_query"]
        )
        
        state["final_experts"] = experts[:20]  # Keep top 20
        self._add_reasoning_trace(state, "Result Reranking", reasoning, f"Reranked {len(experts)} experts")
        
        return state
    
    async def _evaluate_quality(self, state: AutonomousWorkflowState) -> AutonomousWorkflowState:
        """Evaluate result quality"""
        experts = state["final_experts"]
        
        quality_score = self.learning_agent.calculate_quality_score(
            experts,
            state["query"]
        )
        
        state["quality_score"] = quality_score
        
        quality_assessment = f"Quality score: {quality_score:.2f}"
        if quality_score >= self.target_quality:
            quality_assessment += " - Meets target quality"
        else:
            quality_assessment += f" - Below target ({self.target_quality})"
        
        self._add_reasoning_trace(
            state,
            "Quality Evaluation",
            quality_assessment,
            "pass" if quality_score >= self.target_quality else "retry"
        )
        
        return state
    
    async def _generate_suggestions(self, state: AutonomousWorkflowState) -> AutonomousWorkflowState:
        """Generate proactive suggestions"""
        suggestions = self.learning_agent.suggest_improvements(
            state["final_experts"],
            state["query"]
        )
        
        alternative_queries = self.learning_agent.get_alternative_queries(
            state["query"]
        )
        
        state["suggestions"] = suggestions
        state["alternative_queries"] = alternative_queries
        
        if suggestions:
            self._add_reasoning_trace(
                state,
                "Suggestion Generation",
                f"Generated {len(suggestions)} suggestions and {len(alternative_queries)} alternative queries",
                "suggestions_ready"
            )
        
        return state
    
    async def _learn_from_results(self, state: AutonomousWorkflowState) -> AutonomousWorkflowState:
        """Learn from this iteration"""
        self.learning_agent.learn_from_search(
            state["query"],
            state["metadata"]["current_strategy"],
            state["final_experts"]
        )
        
        self._add_reasoning_trace(
            state,
            "Learning Update",
            f"Recorded search results for strategy {state['metadata']['current_strategy']} with quality {state['quality_score']:.2f}",
            "learned"
        )
        
        state["iteration"] += 1
        
        return state
    
    async def _decide_next_action(self, state: AutonomousWorkflowState) -> AutonomousWorkflowState:
        """Decide whether to continue searching"""
        quality_score = state["quality_score"]
        iteration = state["iteration"]
        
        decision_reasoning = []
        
        # Check if we should continue
        if quality_score >= self.target_quality:
            decision_reasoning.append("Target quality achieved")
            state["agent_state"] = AgentState.IDLE
            decision = "complete"
        elif iteration >= self.max_iterations:
            decision_reasoning.append(f"Reached maximum iterations ({self.max_iterations})")
            state["agent_state"] = AgentState.IDLE
            decision = "complete"
        elif len(state["strategies_tried"]) >= 5:
            decision_reasoning.append("Tried all available strategies")
            state["agent_state"] = AgentState.IDLE
            decision = "complete"
        else:
            decision_reasoning.append(f"Quality {quality_score:.2f} below target {self.target_quality}")
            decision_reasoning.append(f"Iteration {iteration} of {self.max_iterations}")
            decision_reasoning.append("Trying next strategy")
            decision = "continue"
        
        self._add_reasoning_trace(
            state,
            "Next Action Decision",
            " | ".join(decision_reasoning),
            decision
        )
        
        return state
    
    def _should_continue(self, state: AutonomousWorkflowState) -> str:
        """Determine if we should continue searching"""
        last_trace = state["reasoning_traces"][-1]
        return "continue" if last_trace.decision == "continue" else "complete"
    
    def _add_reasoning_trace(self, state: AutonomousWorkflowState, step: str, 
                           reasoning: str, decision: str = None):
        """Add reasoning trace"""
        trace = ReasoningTrace(
            step=step,
            reasoning=reasoning,
            decision=decision,
            timestamp=datetime.now().isoformat(),
            confidence=state.get("metadata", {}).get("strategy_confidence", 0.0)
        )
        state["reasoning_traces"].append(trace)
    
    async def run(self, query: str, target_quality: float = 0.8) -> SearchResult:
        """Run autonomous workflow"""
        initial_state = {
            "query": query,
            "search_query": None,
            "experts": [],
            "final_experts": [],
            "metadata": {},
            "reasoning_traces": [],
            "quality_score": 0.0,
            "iteration": 0,
            "strategies_tried": [],
            "agent_state": AgentState.SEARCHING,
            "suggestions": [],
            "alternative_queries": []
        }
        
        self.target_quality = target_quality
        
        result = await self.workflow.ainvoke(initial_state)
        
        return SearchResult(
            experts=result["final_experts"],
            metadata=result["metadata"],
            reasoning_traces=result["reasoning_traces"],
            quality_score=result["quality_score"],
            suggestions=result["suggestions"],
            alternative_queries=result["alternative_queries"]
        )
