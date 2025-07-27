import json
import os
from typing import Dict, List, Optional
from datetime import datetime
from models.schemas import Expert
import logging

logger = logging.getLogger(__name__)

class FeedbackManager:
    def __init__(self, storage_path: str = "data/feedback"):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
        self.feedback_file = os.path.join(storage_path, "user_feedback.json")
        self.feedback_data = self._load_feedback()
    
    def _load_feedback(self) -> Dict:
        """Load feedback data from storage"""
        if os.path.exists(self.feedback_file):
            try:
                with open(self.feedback_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"feedback_records": [], "expert_ratings": {}}
    
    def _save_feedback(self):
        """Save feedback data to storage"""
        try:
            with open(self.feedback_file, 'w') as f:
                json.dump(self.feedback_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving feedback: {e}")
    
    def add_search_feedback(self, session_id: str, query: str, 
                          experts: List[Expert], satisfaction_score: float, 
                          comments: Optional[str] = None):
        """Add feedback for a search session"""
        feedback_record = {
            "session_id": session_id,
            "query": query,
            "expert_ids": [e.id for e in experts[:10]],
            "satisfaction_score": satisfaction_score,
            "comments": comments,
            "timestamp": datetime.now().isoformat()
        }
        
        self.feedback_data["feedback_records"].append(feedback_record)
        
        # Update expert ratings
        for expert in experts[:10]:
            expert_id = str(expert.id)
            if expert_id not in self.feedback_data["expert_ratings"]:
                self.feedback_data["expert_ratings"][expert_id] = {
                    "total_score": 0,
                    "count": 0,
                    "queries": []
                }
            
            rating = self.feedback_data["expert_ratings"][expert_id]
            rating["total_score"] += satisfaction_score
            rating["count"] += 1
            rating["queries"].append(query)
        
        self._save_feedback()
    
    def get_expert_rating(self, expert_id: int) -> Optional[float]:
        """Get average rating for an expert"""
        expert_id_str = str(expert_id)
        if expert_id_str in self.feedback_data["expert_ratings"]:
            rating = self.feedback_data["expert_ratings"][expert_id_str]
            if rating["count"] > 0:
                return rating["total_score"] / rating["count"]
        return None
    
    def get_query_success_rate(self, query_pattern: str) -> float:
        """Get success rate for queries matching a pattern"""
        matching_records = [
            r for r in self.feedback_data["feedback_records"]
            if query_pattern.lower() in r["query"].lower()
        ]
        
        if not matching_records:
            return 0.0
        
        successful = [r for r in matching_records if r["satisfaction_score"] >= 0.7]
        return len(successful) / len(matching_records)
    
