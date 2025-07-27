from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, field_validator, Field
from enum import Enum
from datetime import datetime

class QueryType(Enum):
    DIRECT_EXPERT = "direct_expert"
    PROJECT_BASED = "project_based"
    SKILL_DECOMPOSITION = "skill_decomposition"
    NETWORK_EXPANSION = "network_expansion"
    SEMANTIC_SIMILARITY = "semantic_similarity"

class AgentState(Enum):
    IDLE = "idle"
    SEARCHING = "searching"
    LEARNING = "learning"
    MONITORING = "monitoring"
    SUGGESTING = "suggesting"

class ReasoningTrace(BaseModel):
    step: str
    reasoning: str
    decision: Optional[str] = None
    timestamp: Optional[str] = None
    confidence: float = 0.0

class SearchStrategy(BaseModel):
    name: str
    query_type: QueryType
    success_rate: float = 0.0
    avg_quality_score: float = 0.0
    usage_count: int = 0
    last_used: Optional[datetime] = None

class LearningRecord(BaseModel):
    query: str
    strategy_used: str
    quality_score: float
    user_satisfaction: Optional[float] = None
    expert_ids: List[int]
    timestamp: datetime
    feedback: Optional[str] = None

class Expert(BaseModel):
    id: int
    bio: str
    headline: str
    base_location: Optional[str] = None
    expertise_in_these_geographies: Optional[Union[List[str], str]] = None
    functions: Optional[Union[List[str], str]] = None
    total_years_of_experience: Optional[int] = None
    work_experiences: Optional[List[Dict[str, Any]]] = None
    score: Optional[float] = 0.0
    relevance_explanation: Optional[str] = None
    
    @field_validator('functions', mode='before')
    def parse_functions(cls, v):
        if isinstance(v, str):
            return [item.strip() for item in v.split(',') if item.strip()]
        return v
    
    @field_validator('expertise_in_these_geographies', mode='before')
    def parse_geographies(cls, v):
        if isinstance(v, str):
            try:
                import json
                return json.loads(v)
            except:
                return [item.strip() for item in v.split(',') if item.strip()]
        return v


class Project(BaseModel):
    """Project model for project-based search"""
    id: int
    name: str
    description: str
    topic: str
    agenda_questions: Optional[List[Dict[str, Any]]] = None
    agenda_responses: Optional[str] = None
    expert_ids: Optional[List[int]] = []

class SearchQuery(BaseModel):
    original_query: str
    query_type: QueryType
    enhanced_queries: List[str] = []
    keywords: List[str] = []
    reasoning: Optional[ReasoningTrace] = None
    target_quality: float = 0.8
    max_iterations: int = 10

class SearchResult(BaseModel):
    experts: List[Expert]
    metadata: Dict[str, Any] = {}
    reasoning_traces: List[ReasoningTrace] = []
    quality_score: float = 0.0
    suggestions: List[str] = []
    alternative_queries: List[str] = []
