# Expert Search Agent System (Without LangGraph)

A expert search system that combines vector search, keyword search, and AI-powered query refinement to find relevant experts based on user queries.

## Overview

This system implements a human-like search agent that can search through two types of expert databases:
1. **Normal Experts**: General expert profiles with biographical information
2. **Project-Mapped Experts**: Experts with specific project Q&A responses

The system uses both vector similarity search (semantic) and keyword search (lexical) to provide comprehensive results .

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    HumanLikeSearchAgent                     │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   Planning   │  │   Retrieval  │  │  Fusion/Rerank   │  │
│  │   (_plan)    │  │   (search)   │  │   (reranker)     │  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┴──────────────────────┐
        │                                            │
┌───────▼────────┐                          ┌───────▼────────┐
│  Normal Expert │                          │ Project Expert │
│     Tools      │                          │     Tools      │
├────────────────┤                          ├────────────────┤
│ • Vector Search│                          │ • Vector Search│
│ • Keyword Search                          │ • Keyword Search
└────────────────┘                          └────────────────┘
```

## Components

### 1. **StructuredVectorSearchTool** 
Performs semantic search on normal expert profiles using sentence embeddings.
- Uses SentenceTransformer for embeddings
- Stores vectors in Qdrant vector database
- Aggregates multiple fields (bio, headline, geography, work experiences)

### 2. **StructuredKeywordSearchTool** 
Implements BM25-based keyword search for normal experts.
- Tokenizes text using regex patterns
- Configurable BM25 parameters (k1, b)
- Returns relevance scores

### 3. **AgendaVectorSearchTool** 
Semantic search specifically for project Q&A responses.
- Indexes question-answer pairs from expert project responses
- Links back to expert profiles

### 4. **AgendaKeywordSearchTool** 
Keyword search for project-mapped expert data.

### 5. **AgendaResultsReranker** 
Fuses results from multiple search methods.
- Normalizes scores from different sources
- Applies weighted fusion (alpha parameter)
- Handles ID normalization

### 6. **GeminiQueryRefiner** 
Uses Google's Gemini AI to generate query variants.
- Creates paraphrases for better coverage
- Context-aware refinement

### 7. **HumanLikeSearchAgent** 
The main orchestrator that:
- Plans which tools to use
- Handles clarification requests
- Manages search history
- Applies filters dynamically

## Effects of Building Without LangGraph

### 1. **Manual State Management**
Without LangGraph, the agent must manually track conversation history and state :
```python
self.history: List[Dict[str,Any]] = []
```
This leads to:
- More boilerplate code
- Potential state inconsistencies
- Difficulty in implementing complex workflows

### 2. **No Built-in Tool Orchestration**
The agent manually decides which tools to call in the `_plan` method :
```python
def _plan(self, q: str) -> Dict[str,Any]:
    # Manual prompting to decide tools
```
This results in:
- Custom implementation for each decision point
- No standardized tool interface
- Harder to add new tools

### 3. **Linear Execution Flow**
The current implementation follows a rigid sequence :
1. Plan → 2. Clarify (optional) → 3. Refine → 4. Retrieve → 5. Rerank

Without LangGraph's graph structure:
- No easy branching or conditional flows
- Difficult to implement retries or fallbacks
- No parallel execution paths

### 4. **Manual Error Handling**
Each component needs explicit error handling:
- No automatic retries
- No standardized error propagation
- Manual exception management

### 5. **No Built-in Persistence**
The system lacks:
- Automatic checkpointing
- Recovery from failures
- Long-term memory storage

## Benefits of Using LangGraph

### 1. **Graph-Based Workflow** would allow defining the agent as a state graph:
```python
# With LangGraph (conceptual)
graph = StateGraph(AgentState)
graph.add_node("plan", plan_node)
graph.add_node("search", search_node)
graph.add_edge("plan", "search")
```

### 2. **Automatic State Management**
- Built-in state persistence
- Automatic state transitions
- Type-safe state updates

### 3. **Tool Integration**
- Standardized tool interface
- Automatic tool selection
- Parallel tool execution

### 4. **Error Recovery**
- Built-in retry mechanisms
- Checkpointing for long-running tasks
- Graceful degradation

### 5. **Observability**
- Execution traces
- Performance monitoring
- Debug visualization

### 6. **Scalability**
- Distributed execution support
- Async/await patterns
- Resource management

## Installation

```bash
# Install dependencies
pip install pandas numpy
pip install sentence-transformers
pip install qdrant-client
pip install rank-bm25
pip install google-generativeai
pip install python-dotenv
```

## Usage

### Basic Usage 
```python
# Initialize components
norm_vec = StructuredVectorSearchTool()
norm_kw = StructuredKeywordSearchTool()

# Load and index data
df_norm = pd.read_csv("experts_202505291522.csv")
norm_vec.add_documents(df_norm)
norm_kw.add_documents(df_norm)

# Create agent
agent = HumanLikeSearchAgent(
    norm_vec, norm_kw, proj_vec, proj_kw,
    reranker, refiner,
    initial_k=10, final_n=5
)

# Search
results = agent.search("Find AI experts with 10+ years experience")
```

### Configuration
```python
# Custom reranker with different fusion weight
reranker = AgendaResultsReranker(alpha=0.7)  # More weight to vector search

# Configure query refinement
refiner = GeminiQueryRefiner(
    model_name="gemini-1.5-pro",
    n_variants=5
)
```


