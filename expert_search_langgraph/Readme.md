# Expert Search LangGraph System
This was the First basic Search System , used Gemini LLM

File Structure - 
```
expert_search_langgraph/
├── __init__.py
├── state.py
├── tools/
│   ├── __init__.py
│   ├── vector_search.py
│   ├── keyword_search.py
│   └── reranker.py
├── nodes/
│   ├── __init__.py
│   ├── retrieval.py
│   ├── reranking.py
│   └── refinement.py
├── graph.py
└── main.py
```

Flow of this LangGraph expert search agent with a detailed flowchart and explanation:

## Agent Flow Diagram

```mermaid
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER QUERY INPUT                               │
│                          "machine learning expert"                          │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            INITIAL STATE                                    │
│  • query: "machine learning expert"                                        │
│  • iteration: 0                                                            │
│  • refined_queries: []                                                     │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          RETRIEVE NODE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  Parallel Search Across 4 Sources:                                         │
│                                                                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌────────┐│
│  │ Normal Vector   │  │ Normal Keyword  │  │ Project Vector  │  │Project ││
│  │    Search       │  │  Search (BM25)  │  │    Search       │  │Keyword ││
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  └────┬───┘│
│           │                     │                     │                │    │
│           ▼                     ▼                     ▼                ▼    │
│     [Expert 1,2,3]       [Expert 2,4,5]       [Expert 1,6,7]    [Expert 3,6]│
│       Score: 0.85          Score: 0.72          Score: 0.91       Score:0.8 │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          RERANK NODE                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│  Merge & Score Fusion:                                                      │
│                                                                             │
│  Expert ID │ Vector Score │ Keyword Score │ Fused Score (α=0.6)             │
│  ─────────┼──────────────┼───────────────┼────────────────────              │
│     1      │    0.88      │     0.0       │    0.528                        │
│     2      │    0.85      │     0.72      │    0.798                        │
│     3      │    0.0       │     0.80      │    0.320                        │
│     6      │    0.91      │     0.80      │    0.866                        │
│                                                                             │
│  Quality Score = Max(Fused Scores) = 0.866                                  │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       CHECK & REFINE NODE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  Quality Check:                                                             │
│  • Current Score: 0.866                                                     │
│  • Threshold: 0.5                                                           │
│                                                                             │
│  Decision: Quality > Threshold ✓                                            │
│  Should Refine: FALSE                                                       │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │    Conditional Routing        │
                    │  if should_refine == True     │
                    └───────────────┬───────────────┘
                                    │
                          No ◄──────┴─────► Yes
                           │                  │
                           ▼                  ▼
                ┌──────────────────┐   ┌─────────────────────┐
                │ SELECT FINAL NODE│   │  GEMINI REFINEMENT │
                └─────────┬────────┘   │  • Generate 3       │
                          │            │    query variants   │
                          │            │  • Update state     │
                          │            └──────────┬──────────┘
                          │                       │
                          │                       │ Loop back
                          │                       ▼
                          │              [RETRIEVE NODE]
                          ▼
        ┌─────────────────────────────────────────┐
        │           FINAL RESULTS                 │
        │  Top 5 Experts:                        │
        │  1. Expert 6 - ML Specialist (0.866)  │
        │  2. Expert 2 - Data Scientist (0.798)  │
        │  3. Expert 1 - AI Researcher (0.528)   │
        │  4. Expert 3 - Engineer (0.320)       │
        │  5. Expert 7 - Consultant (0.285)      │
        └─────────────────────────────────────────┘
```

## How the it Works:

#### 1. **Initial State Creation**
When a user enters a query, the system creates an initial state containing:
- The original query
- Empty result lists for each search type
- Quality score of 0
- Iteration counter at 0

#### 2. **Retrieval Phase** 
The agent performs **parallel searches** across 4 different sources:
- **Normal Vector Search**: Semantic search on structured expert bios/headlines
- **Normal Keyword Search**: BM25 search on the same structured data
- **Project Vector Search**: Semantic search on Q&A responses from projects
- **Project Keyword Search**: BM25 search on project Q&A data

Each search returns top-k candidates (default: 10) with relevance scores.

#### 3. **Reranking Phase**
The reranker merges all results using a **fusion algorithm**:
```
Fused Score = α × (normalized vector score) + (1-α) × (normalized keyword score)
```
Where α=0.6 gives 60% weight to semantic similarity and 40% to keyword matching.

The quality score is calculated as the highest fused score among all results.

#### 4. **Quality Check & Refinement Decision**
The agent evaluates whether results are good enough:
- If `quality_score ≥ threshold` (0.5) → Proceed to final selection
- If `quality_score < threshold` AND `iteration = 0` → Refine query

#### 5. **Query Refinement (if needed)**
When quality is poor, the **Gemini LLM** generates 3 query variants:
```
Original: "machine learning expert"
Variants: 
- "AI specialist with ML experience"
- "data scientist machine learning"  
- "artificial intelligence researcher"
```

The agent then **loops back** to retrieval with all queries (original + variants).

#### 6. **Final Selection**
The top 5 experts are selected based on fused scores and returned to the user.

## Key Design Patterns

#### **Stateful Graph Architecture**
- Each node receives and modifies a shared state
- State accumulates information through the flow
- Enables complex decision-making based on previous steps

#### **Conditional Routing**
- The graph can loop back for refinement
- Maximum 1 refinement iteration prevents infinite loops
- Quality threshold acts as a circuit breaker

#### **Hybrid Search Strategy**
- Combines semantic understanding (vectors) with exact matching (keywords)
- Captures both conceptual similarity and specific terminology
- Especially useful for technical expert search

