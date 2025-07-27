from typing import Dict, List, Any
import uuid
from datetime import datetime
import json
import os
from config.settings import SESSION_STORAGE_PATH
import logging

logger = logging.getLogger(__name__)

class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.storage_path = SESSION_STORAGE_PATH
        os.makedirs(self.storage_path, exist_ok=True)
        self._load_sessions()
    
    def _load_sessions(self):
        """Load sessions from storage"""
        try:
            session_files = [f for f in os.listdir(self.storage_path) if f.endswith('.json')]
            for file in session_files[-10:]:  # Load last 10 sessions
                with open(os.path.join(self.storage_path, file), 'r') as f:
                    session_data = json.load(f)
                    session_id = file.replace('.json', '')
                    self.sessions[session_id] = session_data
        except Exception as e:
            logger.error(f"Error loading sessions: {e}")
    
    def _save_session(self, session_id: str):
        """Save session to storage"""
        try:
            session_file = os.path.join(self.storage_path, f"{session_id}.json")
            with open(session_file, 'w') as f:
                json.dump(self.sessions[session_id], f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving session: {e}")
    
    def create_session(self) -> str:
        """Create a new session"""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "created_at": datetime.now().isoformat(),
            "history": [],
            "context": {},
            "metadata": {
                "total_searches": 0,
                "successful_searches": 0,
                "avg_quality_score": 0.0
            }
        }
        self._save_session(session_id)
        return session_id
    
    def add_to_history(self, session_id: str, query: str, response: Dict[str, Any]):
        """Add query and response to session history"""
        if session_id in self.sessions:
            history_entry = {
                "timestamp": datetime.now(),
                "query": query,
                "response": response,
                "quality_score": response.get("quality_score", 0.0)
            }
            
            self.sessions[session_id]["history"].append(history_entry)
            
            # Update metadata
            metadata = self.sessions[session_id]["metadata"]
            metadata["total_searches"] += 1
            
            if response.get("quality_score", 0) >= 0.7:
                metadata["successful_searches"] += 1
            
            # Update average quality score
            history = self.sessions[session_id]["history"]
            total_quality = sum(h.get("quality_score", 0) for h in history)
            metadata["avg_quality_score"] = total_quality / len(history)
            
            self._save_session(session_id)
    
    def get_context(self, session_id: str) -> Dict[str, Any]:
        """Get session context for maintaining conversation"""
        if session_id in self.sessions:
            return self.sessions[session_id]["context"]
        return {}
    
    def update_context(self, session_id: str, context: Dict[str, Any]):
        """Update session context"""
        if session_id in self.sessions:
            self.sessions[session_id]["context"].update(context)
            self._save_session(session_id)
    
    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get session history"""
        if session_id in self.sessions:
            return self.sessions[session_id]["history"]
        return []
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get session statistics"""
        if session_id in self.sessions:
            return self.sessions[session_id]["metadata"]
        return {}
