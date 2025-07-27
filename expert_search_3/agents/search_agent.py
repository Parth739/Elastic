from typing import List, Dict, Any, Tuple
from models.schemas import SearchQuery, Expert, Project, QueryType
from tools.elasticsearch_tools import ElasticsearchClient
from tools.embedding_tools import EmbeddingGenerator
from tools.llm_tools import LLMClient
from config.settings import EXPERT_INDEX, PROJECT_INDEX
import logging

logger = logging.getLogger(__name__)

class SearchAgent:
    def __init__(self):
        self.es_client = ElasticsearchClient()
        self.embedding_gen = EmbeddingGenerator()
        self.llm_client = LLMClient()
    
    async def search_direct_experts(self, search_query: SearchQuery) -> List[Expert]:
        """Direct expert search based on description"""
        all_results = []
        
        for query in [search_query.original_query] + search_query.enhanced_queries:
            query_embedding = self.embedding_gen.generate_embedding(query)
            
            embedding_fields = [
                "combined_embedding",
                "bio_embedding",
                "headline_embedding",
                "profile_embedding"
            ]
            
            text_fields = ["bio", "headline", "functions", "expertise_in_these_geographies"]
            
            for embed_field in embedding_fields:
                results = self.es_client.hybrid_search(
                    index=EXPERT_INDEX,
                    embedding_field=embed_field,
                    query_embedding=query_embedding,
                    text_fields=text_fields,
                    keywords=search_query.keywords,
                    size=20
                )
                all_results.extend(results)
        
        experts_dict = {}
        for result in all_results:
            source = result["_source"]
            expert_id = source["id"]
            
            if expert_id not in experts_dict:
                experts_dict[expert_id] = Expert(
                    id=expert_id,
                    bio=source.get("bio", ""),
                    headline=source.get("headline", ""),
                    base_location=source.get("base_location"),
                    expertise_in_these_geographies=source.get("expertise_in_these_geographies", []),
                    functions=source.get("functions", []),
                    total_years_of_experience=source.get("total_years_of_experience"),
                    work_experiences=source.get("work_experiences", []),
                    score=result["_score"]
                )
            else:
                experts_dict[expert_id].score = max(
                    experts_dict[expert_id].score,
                    result["_score"]
                )
        
        return list(experts_dict.values())
    
    async def search_project_based_experts(self, search_query: SearchQuery) -> List[Expert]:
        """Search experts based on project/agenda matching"""
        logger.info("Starting project-based expert search")
        project_results = []
        
        for query in [search_query.original_query] + search_query.enhanced_queries:
            query_embedding = self.embedding_gen.generate_embedding(query)
            
            embedding_fields = [
                "combined_embedding",
                "description_embedding",
                "topic_embedding",
                "agenda_questions_combined_embedding"
            ]
            
            text_fields = ["description", "topic", "name"]
            
            for embed_field in embedding_fields:
                results = self.es_client.hybrid_search(
                    index=PROJECT_INDEX,
                    embedding_field=embed_field,
                    query_embedding=query_embedding,
                    text_fields=text_fields,
                    keywords=search_query.keywords,
                    size=10
                )
                project_results.extend(results)
        
        expert_ids = set()
        project_descriptions = []
        
        for result in project_results:
            source = result["_source"]
            
            if source.get("agenda_responses"):
                import re
                ids = re.findall(r'expert[_\s]*id[s]?[:\s]*(\d+)', 
                                source["agenda_responses"], re.IGNORECASE)
                expert_ids.update(int(id) for id in ids if id.isdigit())
            
            project_descriptions.append(source.get("description", ""))
        
        logger.info(f"Found {len(expert_ids)} expert IDs from project agenda responses")
        experts = []
        
        if expert_ids:
            expert_results = self.es_client.get_by_ids(EXPERT_INDEX, list(expert_ids))
            for result in expert_results:
                source = result["_source"]
                experts.append(Expert(
                    id=source["id"],
                    bio=source.get("bio", ""),
                    headline=source.get("headline", ""),
                    base_location=source.get("base_location"),
                    expertise_in_these_geographies=source.get("expertise_in_these_geographies", []),
                    functions=source.get("functions", []),
                    total_years_of_experience=source.get("total_years_of_experience"),
                    work_experiences=source.get("work_experiences", []),
                    score=10.0
                ))
        
        if len(experts) < 5 and project_descriptions:
            logger.info("Generating expert profiles from project descriptions")
            
            for desc in project_descriptions[:3]:
                try:
                    expert_profile = await self.llm_client.generate_expert_profile(desc)
                    logger.info(f"Generated profile: {expert_profile[:100]}...")
                    
                    profile_keywords = await self.llm_client.extract_keywords(expert_profile)
                    
                    profile_query = SearchQuery(
                        original_query=expert_profile,
                        query_type=QueryType.DIRECT_EXPERT,
                        enhanced_queries=[],
                        keywords=profile_keywords
                    )
                    
                    profile_experts = await self.search_direct_experts(profile_query)
                    experts.extend(profile_experts[:5])
                    
                except Exception as e:
                    logger.error(f"Error in profile generation/search: {e}")
                    continue
        
        unique_experts = {}
        for expert in experts:
            if expert.id not in unique_experts:
                unique_experts[expert.id] = expert
            else:
                unique_experts[expert.id].score = max(
                    unique_experts[expert.id].score,
                    expert.score
                )
        
        return list(unique_experts.values())
    
    async def search_with_reasoning(self, search_query: SearchQuery) -> Tuple[List[Expert], str]:
        """Search with reasoning explanation"""
        reasoning_parts = []
        
        if search_query.query_type == QueryType.DIRECT_EXPERT:
            reasoning_parts.append("Performing direct expert search:")
            reasoning_parts.append(f"- Using {len(search_query.enhanced_queries) + 1} query variations")
            reasoning_parts.append(f"- Searching with {len(search_query.keywords)} keywords")
            reasoning_parts.append("- Combining semantic and keyword search results")
            
            experts = await self.search_direct_experts(search_query)
            
            reasoning_parts.append(f"- Found {len(experts)} unique experts")
            
        else:
            reasoning_parts.append("Performing project-based expert search:")
            reasoning_parts.append("- First searching for similar projects")
            
            experts = await self.search_project_based_experts(search_query)
            
            reasoning_parts.append(f"- Searched project database for matches")
            reasoning_parts.append(f"- Found {len(experts)} relevant experts")
            
            if len(experts) == 0:
                reasoning_parts.append("- No direct expert mappings found, generated ideal profiles")
        
        reasoning = "\n".join(reasoning_parts)
        return experts, reasoning
