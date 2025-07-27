# Utils

## What FeedbackManager Does

### Purpose
The FeedbackManager acts as a **learning system** that collects user satisfaction data to understand which searches work well and which experts provide the best matches.

### How It Works

#### 1. **Data Collection Process**
When a user completes a search and provides feedback:
```python
# User searches for "ML expert"
# System returns 10 experts
# User rates satisfaction as 0.8 (80% satisfied)

feedback_mgr.add_search_feedback(
    session_id="abc-123",
    query="ML expert needed for computer vision",
    experts=[expert1, expert2, ...],  # The experts shown
    satisfaction_score=0.8,
    comments="Good results, found what I needed"
)
```

#### 2. **What Happens Internally**
The manager performs several actions:

**Creates a Feedback Record:**
- Timestamps when feedback was given
- Links feedback to specific search query
- Stores which experts were shown
- Records satisfaction level

**Updates Expert Ratings:**
- Each expert shown accumulates ratings
- Tracks which queries led to their selection
- Calculates running average satisfaction

**Persists to Disk:**
- Saves all data to JSON file
- Ensures data survives system restarts

#### 3. **Data Analysis Capabilities**

**Expert Performance Tracking:**
```python
# If Expert ID 123 has been shown in 10 searches:
# - 5 searches with 0.9 satisfaction
# - 3 searches with 0.7 satisfaction  
# - 2 searches with 0.5 satisfaction
# Average rating = (5*0.9 + 3*0.7 + 2*0.5) / 10 = 0.76
```

**Query Pattern Analysis:**
```python
# For all queries containing "machine learning":
# - 20 total searches
# - 16 with satisfaction >= 0.7 (successful)
# Success rate = 16/20 = 80%
```

### Real-World Impact

1. **Improving Search Rankings**: Experts with higher average ratings can be boosted in future searches
2. **Understanding User Needs**: Identify which query types struggle to find good matches
3. **Quality Assurance**: Track overall system performance over time

## What SessionManager Does

### Purpose
The SessionManager maintains **conversation continuity** and **user context** across multiple interactions, enabling personalized and context-aware searches.

### How It Works

#### 1. **Session Creation**
When a user starts interacting:
```python
session_id = session_mgr.create_session()
# Creates unique ID: "550e8400-e29b-41d4-a716-446655440000"
# Initializes empty history and context
```

#### 2. **History Tracking**
For each search in the session:
```python
# User searches for "Python developer"
# System records:
{
    "timestamp": "2024-01-15T10:31:00",
    "query": "Python developer with AWS",
    "response": {
        "experts": [...],
        "quality_score": 0.85
    }
}
```

#### 3. **Context Management**
The system learns from interactions:
```python
# After first search for "Python developer with AWS"
context = {
    "preferred_skills": ["Python", "AWS"],
    "recent_queries": ["Python developer with AWS"]
}

# After second search for "remote work available"
context = {
    "preferred_skills": ["Python", "AWS"],
    "location_preference": "remote",
    "recent_queries": ["Python developer with AWS", "remote work available"]
}
```

#### 4. **Automatic Metrics Calculation**
The manager tracks:
- **Total searches**: How many queries in this session
- **Successful searches**: Queries with quality_score >= 0.7
- **Average quality**: Overall session performance

### Real-World Impact

1. **Conversational Search**:
   ```
   User: "Find me a Python developer"
   System: [Shows Python developers]
   User: "Only remote ones"
   System: [Filters previous results for remote workers]
   ```

2. **Personalization**:
   - Remember user preferences
   - Tailor future searches based on history
   - Avoid asking for same information repeatedly

3. **Session Analytics**:
   - Identify struggling users (low success rate)
   - Understand typical search patterns
   - Optimize for common workflows

## How They Work Together

### Integrated Workflow Example

```python
# 1. User starts new session
session_id = session_mgr.create_session()

# 2. User searches
query = "Need ML expert for computer vision project"
results = await workflow.run(query)

# 3. System saves to history with quality metrics
session_mgr.add_to_history(session_id, query, {
    "experts": results["experts"],
    "quality_score": 0.85
})

# 4. System updates context for future searches
session_mgr.update_context(session_id, {
    "project_type": "computer_vision",
    "expertise_needed": ["ML", "CV", "Python"]
})

# 5. User provides feedback
feedback_mgr.add_search_feedback(
    session_id=session_id,
    query=query,
    experts=results["experts"],
    satisfaction_score=0.9,
    comments="Perfect match!"
)

# 6. System can now:
# - Boost these experts for similar queries
# - Know this user prefers CV experts
# - Track that CV queries have high success
```

## Key Benefits

### 1. **Continuous Improvement**
- Learn which experts best match certain queries
- Identify gaps in expert coverage
- Optimize search algorithms based on feedback

### 2. **Enhanced User Experience**
- Remember user preferences
- Provide contextual results
- Reduce repetitive information requests

## Storage and Persistence

Both managers use **JSON file storage** for simplicity:

```
data/
├── feedback/
│   └── user_feedback.json      # All feedback data
└── sessions/
    ├── session-123.json        # Individual session files
    ├── session-456.json
    └── ...
```

This approach:
- **Simple**: No database required
- **Portable**: Easy to backup/transfer
- **Human-readable**: Can inspect/debug easily
- **Sufficient**: For moderate usage levels

## Summary

The utils directory provides the **memory and learning capabilities** of the expert search system:

- **FeedbackManager**: Learns from user satisfaction to improve future searches
- **SessionManager**: Maintains context for personalized, conversational interactions

