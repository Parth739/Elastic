import json
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from models.schemas import LearningRecord, SearchStrategy, QueryType
import pickle
import logging

logger = logging.getLogger(__name__)

class LearningStorage:
    def __init__(self, storage_path: str = "data/learning"):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
        
        self.strategies_file = os.path.join(storage_path, "strategies.pkl")
        self.learning_records_file = os.path.join(storage_path, "learning_records.pkl")
        self.query_patterns_file = os.path.join(storage_path, "query_patterns.pkl")
        
        self.strategies = self._load_strategies()
        self.learning_records = self._load_learning_records()
        self.query_patterns = self._load_query_patterns()
    
    def _load_strategies(self) -> Dict[str, SearchStrategy]:
        """Load search strategies from storage"""
        if os.path.exists(self.strategies_file):
            try:
                with open(self.strategies_file, 'rb') as f:
                    return pickle.load(f)
            except:
                pass
        
        # Initialize default strategies
        return {
            "direct_expert": SearchStrategy(
                name="direct_expert",
                query_type=QueryType.DIRECT_EXPERT,
                success_rate=0.7
            ),
            "project_based": SearchStrategy(
                name="project_based",
                query_type=QueryType.PROJECT_BASED,
                success_rate=0.6
            ),
            "skill_decomposition": SearchStrategy(
                name="skill_decomposition",
                query_type=QueryType.SKILL_DECOMPOSITION,
                success_rate=0.65
            ),
            "network_expansion": SearchStrategy(
                name="network_expansion",
                query_type=QueryType.NETWORK_EXPANSION,
                success_rate=0.5
            ),
            "semantic_similarity": SearchStrategy(
                name="semantic_similarity",
                query_type=QueryType.SEMANTIC_SIMILARITY,
                success_rate=0.75
            )
        }
    
    def _load_learning_records(self) -> List[LearningRecord]:
        """Load learning records from storage"""
        if os.path.exists(self.learning_records_file):
            try:
                with open(self.learning_records_file, 'rb') as f:
                    return pickle.load(f)
            except:
                pass
        return []
    
    def _load_query_patterns(self) -> Dict[str, Dict]:
        """Load successful query patterns"""
        if os.path.exists(self.query_patterns_file):
            try:
                with open(self.query_patterns_file, 'rb') as f:
                    return pickle.load(f)
            except:
                pass
        return {}
    
    def save_all(self):
        """Save all data to storage"""
        try:
            with open(self.strategies_file, 'wb') as f:
                pickle.dump(self.strategies, f)
            
            with open(self.learning_records_file, 'wb') as f:
                pickle.dump(self.learning_records, f)
            
            with open(self.query_patterns_file, 'wb') as f:
                pickle.dump(self.query_patterns, f)
                
            logger.info("Learning data saved successfully")
        except Exception as e:
            logger.error(f"Error saving learning data: {e}")
    
    def add_learning_record(self, record: LearningRecord):
        """Add a new learning record"""
        self.learning_records.append(record)
        
        # Update strategy statistics
        if record.strategy_used in self.strategies:
            strategy = self.strategies[record.strategy_used]
            strategy.usage_count += 1
            strategy.last_used = record.timestamp
            
            # Update success rate with exponential moving average
            alpha = 0.1  # Learning rate
            strategy.success_rate = (1 - alpha) * strategy.success_rate + alpha * record.quality_score
            strategy.avg_quality_score = (1 - alpha) * strategy.avg_quality_score + alpha * record.quality_score
        
        # Save periodically
        if len(self.learning_records) % 10 == 0:
            self.save_all()
    
    def get_best_strategy_for_query(self, query: str) -> Optional[str]:
        """Get the best strategy based on historical performance"""
        # Check if we have a similar query pattern
        for pattern, data in self.query_patterns.items():
            if pattern.lower() in query.lower():
                return data.get("best_strategy")
        
        # Return strategy with highest success rate
        best_strategy = max(self.strategies.values(), key=lambda s: s.success_rate)
        return best_strategy.name
    
    def update_query_pattern(self, query: str, strategy: str, quality_score: float):
        """Update successful query patterns"""
        # Extract key phrases from query
        key_phrases = [phrase for phrase in query.lower().split() if len(phrase) > 4]
        
        for phrase in key_phrases:
            if phrase not in self.query_patterns:
                self.query_patterns[phrase] = {
                    "best_strategy": strategy,
                    "avg_quality": quality_score,
                    "count": 1
                }
            else:
                # Update with better strategy if found
                current_quality = self.query_patterns[phrase]["avg_quality"]
                if quality_score > current_quality:
                    self.query_patterns[phrase]["best_strategy"] = strategy
                    self.query_patterns[phrase]["avg_quality"] = quality_score
                self.query_patterns[phrase]["count"] += 1
    
    def get_recent_successful_queries(self, limit: int = 10) -> List[LearningRecord]:
        """Get recent successful searches"""
        successful_records = [r for r in self.learning_records if r.quality_score > 0.7]
        return sorted(successful_records, key=lambda r: r.timestamp, reverse=True)[:limit]
