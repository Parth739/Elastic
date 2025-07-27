# Workflows

This directory contains the workflow orchestration layer for the expert search system, implementing state-based workflows using LangGraph.

## Overview

The workflows directory includes two main workflow implementations:

1. **ExpertSearchWorkflow** (`expert_search_workflow.py`) - Basic expert search with quality checks and limited retry logic, this approach is more determinstic one in which we create the flow in the langgraph and it is happens in that order only.
2. **AutonomousWorkflow** (`autonomous_workflow.py`) - Extended autonomous workflow with more sophisticated decision-making capabilities , while this approach is more autonomous, in which we let the LLM decide which step to do , considering everything , also the feedback

## 1. ExpertSearchWorkflow

The primary workflow for handling expert search requests with intelligent query analysis, search execution, result reranking, and quality assurance.

### Architecture

#### State Management

The workflow maintains state throughout execution:

```python
class WorkflowState(TypedDict):
    query: str                              # Original user query
    search_query: SearchQuery              # Analyzed query structure
    experts: List[Expert]                  # Raw search results
    final_experts: List[Expert]            # Reranked results
    metadata: Dict[str, Any]               # Process metadata
    reasoning_traces: List[ReasoningTrace] # Decision audit trail
```

#### Workflow Graph Structure

```
Start → Analyze Query → Search Experts → Rerank Results → Quality Check
                              ↑                                  |
                              |←←← (retry on failure) ←←←←←←←←←←|
                                                                |
                                                              End
```

### Core Nodes

#### 1. Analyze Query Node
- Processes user input to understand intent
- Determines search strategy (direct vs project-based)
- Extracts keywords and requirements
- Provides reasoning traces for decisions

#### 2. Search Experts Node
- Executes appropriate search strategy
- Handles both direct expert and project-based searches
- Logs search reasoning and results count
- Includes fallback mechanisms

#### 3. Rerank Results Node
- Optimizes result ordering based on relevance
- Applies LLM-based reranking when available
- Falls back to basic scoring if needed
- Limits to top 10 results

#### 4. Quality Check Node
- Validates result quality
- Checks for:
  - Presence of results
  - Minimum count threshold (3+ experts)
  - High relevance scores (>1.0)
- Determines retry necessity

### Features

#### Reasoning Traces
Every major decision includes transparent reasoning:

```python
{
    "step": "Query Analysis",
    "reasoning": "Query contains 'project' keyword and implementation details",
    "decision": "PROJECT_BASED",
    "timestamp": "2024-01-15T10:30:00"
}
```

#### Retry Logic
- Maximum 2 retry attempts
- Triggered by quality check failures
- Includes retry reasoning in traces

#### Error Handling
- Try-except patterns with graceful fallbacks
- Comprehensive logging
- Maintains functionality during service failures

### Usage

```python
from workflows.expert_search_workflow import ExpertSearchWorkflow

# Initialize workflow
workflow = ExpertSearchWorkflow()

# Execute search
result = await workflow.run("I need a machine learning expert for computer vision")

# Access results
experts = result["experts"]              # List of Expert objects
metadata = result["metadata"]            # Process metadata
reasoning_traces = result["reasoning_traces"]  # Decision log
```

### Example Output

```python
{
    "experts": [
        {
            "id": "exp-123",
            "name": "Dr. Jane Smith",
            "headline": "Computer Vision Researcher",
            "bio": "10+ years in ML/CV...",
            "skills": ["PyTorch", "OpenCV", "Deep Learning"],
            "score": 1.85
        }
        # ... more experts
    ],
    "metadata": {
        "query_type": "PROJECT_BASED",
        "search_count": 25,
        "quality_score": True,
        "retry_count": 0
    },
    "reasoning_traces": [
        {
            "step": "Query Analysis",
            "reasoning": "Identified project-based request",
            "decision": "PROJECT_BASED",
            "timestamp": "2024-01-15T10:30:00"
        },
        {
            "step": "Search Strategy",
            "reasoning": "Using project-based search strategy...",
            "decision": "PROJECT_BASED"
        },
        {
            "step": "Search Execution",
            "reasoning": "Hybrid search executed",
            "decision": "Found 25 experts"
        },
        {
            "step": "Result Reranking",
            "reasoning": "Reranked based on CV expertise",
            "decision": "Reranked to top 10 experts"
        },
        {
            "step": "Quality Assessment",
            "reasoning": "Found 10 experts | Sufficient count | High scores",
            "decision": "Pass"
        }
    ]
}
```

## 2. AutonomousWorkflow

An extended workflow implementation designed for more autonomous operation with advanced decision-making capabilities.

### Expected Features

Based on the workflow structure, the autonomous workflow likely includes:

- **Extended Retry Logic**: More sophisticated retry strategies
- **Self-Correction**: Ability to modify search parameters automatically
- **Multi-Step Planning**: Breaking complex queries into sub-tasks
- **Learning Integration**: Adapting based on previous results
- **Advanced Quality Metrics**: More nuanced quality assessment

### Expected Nodes

The autonomous workflow would extend the basic workflow with additional nodes:

- **Query Decomposition**: Breaking complex queries into sub-queries
- **Strategy Selection**: Dynamic strategy selection based on context
- **Result Synthesis**: Combining results from multiple search strategies
- **Feedback Integration**: Learning from quality check results

## Configuration

Both workflows depend on these agent instances:

```python
# Required agents (from agents directory)
self.query_analyzer = QueryAnalyzer()    # Query understanding
self.search_agent = SearchAgent()        # Search execution
self.reranker = Reranker()              # Result optimization
```





