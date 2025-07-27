from typing import List, Tuple
from models.schemas import Expert, SearchQuery
from tools.llm_tools import LLMClient
import logging

logger = logging.getLogger(__name__)

class Reranker:
    def __init__(self):
        self.llm_client = LLMClient()
    
    async def rerank_experts(self, experts: List[Expert], 
                           search_query: SearchQuery) -> List[Expert]:
        """Original rerank method"""
        if not experts:
            return experts
        
        # Validate experts are proper Expert objects
        valid_experts = []
        for expert in experts:
            if isinstance(expert, Expert):
                valid_experts.append(expert)
            else:
                logger.warning(f"Skipping non-Expert object: {type(expert)}")
        
        if not valid_experts:
            return experts
        
        expert_dicts = []
        for expert in valid_experts[:10]:  # Limit to top 10
            expert_dicts.append({
                "id": expert.id,
                "bio": expert.bio[:200] if expert.bio else "",
                "headline": expert.headline[:100] if expert.headline else "",
                "functions": expert.functions if expert.functions else [],
                "total_years_of_experience": expert.total_years_of_experience or 0
            })
        
        reranked_dicts = await self.llm_client.rerank_results(
            search_query.original_query,
            expert_dicts
        )
        
        # Create mapping
        id_to_expert = {expert.id: expert for expert in valid_experts}
        reranked_experts = []
        
        # Build reranked list
        for dict_item in reranked_dicts:
            if isinstance(dict_item, dict) and 'id' in dict_item:
                expert_id = dict_item.get("id")
                if expert_id in id_to_expert:
                    reranked_experts.append(id_to_expert[expert_id])
        
        # Add remaining experts
        reranked_ids = {e.id for e in reranked_experts}
        for expert in valid_experts:
            if expert.id not in reranked_ids:
                reranked_experts.append(expert)
        
        return reranked_experts if reranked_experts else experts
    
    async def rerank_with_reasoning(self, experts: List[Expert], 
                                   search_query: SearchQuery) -> Tuple[List[Expert], str]:
        """Rerank experts with reasoning"""
        if not experts:
            return experts, "No experts to rerank"
        
        if len(experts) <= 3:
            return experts, f"Only {len(experts)} experts found, no reranking needed"
        
        # Validate experts
        valid_experts = []
        for expert in experts:
            if isinstance(expert, Expert) and hasattr(expert, 'id'):
                valid_experts.append(expert)
            else:
                logger.warning(f"Invalid expert object: {type(expert)}")
        
        if not valid_experts:
            return experts, "No valid expert data for reranking"
        
        # Prepare data for LLM
        expert_dicts = []
        for i, expert in enumerate(valid_experts[:10]):  # Limit to top 10
            try:
                expert_dict = {
                    "id": expert.id,
                    "bio": (expert.bio[:200] + "...") if expert.bio and len(expert.bio) > 200 else (expert.bio or "No bio"),
                    "headline": expert.headline or "No headline",
                    "functions": expert.functions if expert.functions else [],
                    "total_years_of_experience": expert.total_years_of_experience or 0
                }
                expert_dicts.append(expert_dict)
            except Exception as e:
                logger.error(f"Error processing expert {i}: {e}")
                continue
        
        if not expert_dicts:
            return experts, "Could not process experts for reranking"
        
        try:
            # Get reranked results from LLM
            reranked_dicts, reasoning = await self.llm_client.rerank_with_reasoning(
                search_query.original_query,
                expert_dicts
            )
            
            # Map back to Expert objects
            id_to_expert = {expert.id: expert for expert in valid_experts}
            reranked_experts = []
            
            # Process reranked results
            if isinstance(reranked_dicts, list):
                for item in reranked_dicts:
                    if isinstance(item, dict) and 'id' in item:
                        expert_id = item.get('id')
                        if expert_id in id_to_expert:
                            reranked_experts.append(id_to_expert[expert_id])
            
            # Add any remaining experts
            reranked_ids = {e.id for e in reranked_experts}
            for expert in valid_experts:
                if expert.id not in reranked_ids:
                    reranked_experts.append(expert)
            
            # Add experts beyond top 10 if any
            if len(experts) > 10:
                for expert in experts[10:]:
                    if expert.id not in reranked_ids:
                        reranked_experts.append(expert)
            
            if reranked_experts:
                return reranked_experts, reasoning
            else:
                return experts, f"Reranking incomplete, using original order. Reason: {reasoning}"
                
        except Exception as e:
            logger.error(f"Reranking error: {e}")
            return experts, f"Reranking failed: {str(e)}"
