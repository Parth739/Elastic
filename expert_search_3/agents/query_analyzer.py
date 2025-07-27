from typing import Dict, Any, List, Tuple
from models.schemas import QueryType, SearchQuery, ReasoningTrace
from tools.llm_tools import LLMClient
import logging

logger = logging.getLogger(__name__)

class QueryAnalyzer:
    def __init__(self):
        self.llm_client = LLMClient()
    
    async def analyze(self, query: str) -> SearchQuery:
        """Original analyze method"""
        analysis = await self.llm_client.analyze_query(query)
        
        query_type = QueryType.PROJECT_BASED if analysis.get("query_type") == "project_based" else QueryType.DIRECT_EXPERT
        
        enhanced_queries = await self.llm_client.enhance_query(query)
        keywords = await self.llm_client.extract_keywords(query)
        
        return SearchQuery(
            original_query=query,
            query_type=query_type,
            enhanced_queries=enhanced_queries,
            keywords=keywords
        )
    
    async def analyze_with_reasoning(self, query: str) -> Tuple[SearchQuery, List[ReasoningTrace]]:
        """Analyze query and return reasoning traces"""
        reasoning_traces = []
        
        try:
            analysis, analysis_reasoning = await self.llm_client.analyze_query_with_reasoning(query)
            
            reasoning_traces.append(ReasoningTrace(
                step="Query Analysis",
                reasoning=analysis_reasoning,
                decision=analysis.get("query_type", "direct_expert"),
                confidence=0.8
            ))
            
            query_type = QueryType.PROJECT_BASED if analysis.get("query_type") == "project_based" else QueryType.DIRECT_EXPERT
            
            enhanced_queries, enhance_reasoning = await self.llm_client.enhance_query_with_reasoning(query)
            
            reasoning_traces.append(ReasoningTrace(
                step="Query Enhancement",
                reasoning=enhance_reasoning,
                decision=f"Generated {len(enhanced_queries)} query variations",
                confidence=0.9
            ))
            
            keywords, keyword_reasoning = await self.llm_client.extract_keywords_with_reasoning(query)
            
            reasoning_traces.append(ReasoningTrace(
                step="Keyword Extraction",
                reasoning=keyword_reasoning,
                decision=f"Extracted {len(keywords)} keywords",
                confidence=0.85
            ))
            
            search_query = SearchQuery(
                original_query=query,
                query_type=query_type,
                enhanced_queries=enhanced_queries,
                keywords=keywords,
                reasoning=reasoning_traces[0]
            )
            
            return search_query, reasoning_traces
            
        except Exception as e:
            logger.error(f"Error in query analysis: {e}")
            # Fallback
            search_query = SearchQuery(
                original_query=query,
                query_type=QueryType.DIRECT_EXPERT,
                enhanced_queries=[query],
                keywords=query.split()[:5]
            )
            reasoning_traces.append(ReasoningTrace(
                step="Query Analysis",
                reasoning="Using fallback analysis due to error",
                decision="direct_expert",
                confidence=0.5
            ))
            return search_query, reasoning_traces
