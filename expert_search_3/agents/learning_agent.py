from typing import List, Dict, Any, Optional, Tuple
from models.schemas import SearchQuery, Expert, LearningRecord, SearchStrategy
from storage.learning_storage import LearningStorage
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class LearningAgent:
    def __init__(self):
        self.storage = LearningStorage()
        self.current_session_learnings = []
    
    async def select_strategy(self, query: str, previous_attempts: List[str] = []) -> Tuple[str, float]:
        """Select the best strategy based on learning"""
        # Get historical best strategy
        best_strategy = self.storage.get_best_strategy_for_query(query)
        
        # Avoid strategies we've already tried
        available_strategies = [
            s for s in self.storage.strategies.keys() 
            if s not in previous_attempts
        ]
        
        if not available_strategies:
            # If we've tried everything, pick the one with highest general success
            best_strategy = max(
                self.storage.strategies.values(), 
                key=lambda s: s.success_rate
            ).name
            confidence = 0.5
        else:
            # Pick best available strategy
            if best_strategy in available_strategies:
                confidence = self.storage.strategies[best_strategy].success_rate
            else:
                # Pick best from available
                best_available = max(
                    [self.storage.strategies[s] for s in available_strategies],
                    key=lambda s: s.success_rate
                )
                best_strategy = best_available.name
                confidence = best_available.success_rate
        
        logger.info(f"Selected strategy: {best_strategy} with confidence: {confidence}")
        return best_strategy, confidence
    
    def calculate_quality_score(self, experts: List[Expert], query: str) -> float:
        """Calculate quality score for search results"""
        if not experts:
            return 0.0
        
        # Multiple quality factors
        factors = {
            "has_results": 1.0 if len(experts) > 0 else 0.0,
            "sufficient_count": min(len(experts) / 10, 1.0),
            "high_relevance": sum(1 for e in experts if e.score > 5.0) / len(experts),
            "diversity": len(set(e.functions[0] if e.functions else "" for e in experts)) / max(len(experts), 1),
            "experience_match": sum(1 for e in experts if e.total_years_of_experience and e.total_years_of_experience > 5) / len(experts)
        }
        
        # Weighted average
        weights = {
            "has_results": 0.2,
            "sufficient_count": 0.2,
            "high_relevance": 0.3,
            "diversity": 0.15,
            "experience_match": 0.15
        }
        
        quality_score = sum(factors[k] * weights[k] for k in factors)
        return quality_score
    
    def learn_from_search(self, query: str, strategy: str, experts: List[Expert], 
                         user_feedback: Optional[float] = None):
        """Learn from a search interaction"""
        quality_score = self.calculate_quality_score(experts, query)
        
        record = LearningRecord(
            query=query,
            strategy_used=strategy,
            quality_score=quality_score,
            user_satisfaction=user_feedback,
            expert_ids=[e.id for e in experts[:10]],
            timestamp=datetime.now()
        )
        
        self.storage.add_learning_record(record)
        
        # Update query patterns if successful
        if quality_score > 0.7:
            self.storage.update_query_pattern(query, strategy, quality_score)
        
        self.current_session_learnings.append(record)
    
    def suggest_improvements(self, current_results: List[Expert], query: str) -> List[str]:
        """Suggest improvements based on learning"""
        suggestions = []
        
        # Analyze current results
        quality_score = self.calculate_quality_score(current_results, query)
        
        if quality_score < 0.5:
            suggestions.append("Try breaking down your query into specific skills")
            suggestions.append("Consider searching for related project types")
        
        if len(current_results) < 5:
            suggestions.append("Broaden your search terms")
            suggestions.append("Try removing specific requirements")
        
        # Look for similar successful queries
        similar_queries = [
            r for r in self.storage.get_recent_successful_queries()
            if any(word in r.query.lower() for word in query.lower().split())
        ]
        
        if similar_queries:
            suggestions.append(f"Similar successful search: '{similar_queries[0].query}'")
        
        return suggestions
    
    def get_alternative_queries(self, original_query: str) -> List[str]:
        """Generate alternative queries based on learning"""
        alternatives = []
        
        # Find successful patterns
        successful_patterns = [
            pattern for pattern, data in self.storage.query_patterns.items()
            if data["avg_quality"] > 0.7
        ]
        
        # Create variations
        for pattern in successful_patterns[:3]:
            if pattern not in original_query.lower():
                alternatives.append(f"{original_query} {pattern}")
        
        # Add queries from successful searches
        recent_successful = self.storage.get_recent_successful_queries(5)
        for record in recent_successful:
            if record.query != original_query:
                alternatives.append(record.query)
        
        return alternatives[:5]
