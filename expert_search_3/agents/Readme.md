# Agents

## Overview

The Agents module implements a multi-agent system for intelligent expert search, featuring:
- Query understanding and enhancement
- Adaptive search strategies with learning
- Multi-modal search (direct expert search and project-based search)
- Result reranking with reasoning
- Continuous learning from user interactions

## Agent Components

### 1. Query Analyzer (`query_analyzer.py`)

Analyzes and enhances user queries for better search results.

**Key Features:**
- Query type detection (direct expert vs project-based)
- Query enhancement and variation generation
- Keyword extraction
- Reasoning trace generation for debugging and checking modek performance

**Main Methods:**
- `analyze(query: str)` - Basic query analysis
- `analyze_with_reasoning(query: str)` - Analysis with detailed reasoning traces

### 2. Search Agent (`search_agent.py`)

Performs the actual search operations using multiple strategies.

**Key Features:**
- Direct expert search using semantic and keyword matching
- Project-based expert discovery
- Hybrid search combining embeddings and text search
- Multi-field searching (bio, headline, functions, expertise)

**Main Methods:**
- `search_direct_experts(search_query: SearchQuery)` - Direct expert search
- `search_project_based_experts(search_query: SearchQuery)` - Find experts through projects
- `search_with_reasoning(search_query: SearchQuery)` - Search with reasoning explanation

### 3. Reranker (`reranker.py`)

Intelligently reorders search results based on relevance to the query.

**Key Features:**
- LLM-based relevance scoring
- Context-aware reranking
- Reasoning explanations for ranking decisions
- Handles edge cases (few results, invalid data)

**Main Methods:**
- `rerank_experts(experts: List[Expert], search_query: SearchQuery)` - Basic reranking
- `rerank_with_reasoning(experts: List[Expert], search_query: SearchQuery)` - Reranking with explanations

### 4. Learning Agent (`learning_agent.py`)

Learns from search interactions to improve future searches.

**Key Features:**
- Strategy selection based on historical performance
- Quality score calculation for search results
- Query pattern recognition
- Improvement suggestions
- Alternative query generation

**Main Methods:**
- `select_strategy(query: str, previous_attempts: List[str])` - Choose best search strategy
- `learn_from_search(query: str, strategy: str, experts: List[Expert])` - Record search outcomes
- `suggest_improvements(current_results: List[Expert], query: str)` - Provide search tips
- `get_alternative_queries(original_query: str)` - Generate query variations

## Quality Scoring

The Learning Agent calculates quality scores based on:
- Result count (sufficient experts found)
- Relevance scores (high-scoring matches)
- Diversity (variety in functions/expertise)
- Experience match (years of experience alignment)

## Search Strategies

The system supports multiple search strategies:
- **Direct Expert Search**: Searches expert profiles directly
- **Project-Based Search**: Finds experts through project involvement
- **Hybrid Approach**: Combines multiple search methods
