# Tools 

## Overview

The tools folder provides three essential services:
- **Elasticsearch operations** for data retrieval and search
- **Embedding generation** for semantic understanding
- **LLM integration** for intelligent query processing

## Components

### 1. ElasticsearchClient (`elasticsearch_client.py`)

A comprehensive client for interacting with Elasticsearch indices containing expert and project data.

#### Key Features:
- **Semantic Search**: Uses KNN (k-nearest neighbors) for vector similarity search
- **Keyword Search**: Traditional text-based search with fuzzy matching support
- **Hybrid Search**: Combines semantic and keyword approaches with weighted scoring
- **Batch Operations**: Retrieve documents by IDs or get recent entries

#### Main Methods:

```python
# Initialize the client
es_client = ElasticsearchClient()

# Semantic search using embeddings
results = es_client.semantic_search(
    index="experts",
    embedding_field="embedding",
    query_embedding=[...],  # Vector representation
    size=10
)

# Keyword-based search
results = es_client.keyword_search(
    index="experts", 
    fields=["bio", "headline", "skills"],
    keywords=["machine learning", "python"],
    size=10
)

# Hybrid search (best of both)
results = es_client.hybrid_search(
    index="experts",
    embedding_field="embedding",
    query_embedding=[...],
    text_fields=["bio", "headline", "skills"],
    keywords=["data scientist"],
    size=10
)
```


### 2. EmbeddingGenerator (`embedding_generator.py`)

Handles text-to-vector conversion using sentence transformers for semantic search capabilities.

#### Key Features:
- **Single & Batch Processing**: Generate embeddings for one or multiple texts
- **Similarity Computation**: Calculate cosine similarity between embeddings
- **Fallback Handling**: Returns zero vectors if model fails

#### Main Methods:

```python
# Initialize generator
embedding_gen = EmbeddingGenerator()

# Generate single embedding
embedding = embedding_gen.generate_embedding("Looking for ML expert")

# Batch generation
embeddings = embedding_gen.generate_embeddings([
    "Machine learning specialist",
    "Data scientist with Python experience"
])

# Compute similarity
similarity = embedding_gen.compute_similarity(embedding1, embedding2)
```

#### Configuration:
- Uses model specified in `EMBEDDING_MODEL` setting
- Default: `sentence-transformers/all-MiniLM-L6-v2`
- Produces 384-dimensional vectors

### 3. LLMClient (`llm_client.py`)

Integrates with language models for intelligent query understanding and result optimization.

#### function s
- **Query Analysis**: Understands user intent with dual strategy support
- **Query Enhancement**: Generates improved search variations
- **Keyword Extraction**: Identifies important search terms
- **Result Reranking**: Reorders results based on relevance
- **Reasoning Traces**: Provides transparent decision-making process

#### Main Methods:

```python
# Initialize client
llm_client = LLMClient()

# Analyze user query with reasoning
analysis, reasoning = await llm_client.analyze_query_with_reasoning(
    "I need a machine learning expert for computer vision"
)

# Enhance query for better results
variations, reasoning = await llm_client.enhance_query_with_reasoning(
    "data scientist", 
    count=3
)

# Extract keywords
keywords, reasoning = await llm_client.extract_keywords_with_reasoning(
    "Senior Python developer with AWS experience"
)

# Rerank search results
reranked, reasoning = await llm_client.rerank_with_reasoning(
    query="ML engineer",
    results=search_results
)

# Generate expert profile from project description
profile = await llm_client.generate_expert_profile(
    "Building a recommendation system using deep learning"
)
```

#### Dual Search Strategies:
1. **Direct Expert Search**: When users explicitly ask for specific expertise
2. **Project-Based Search**: When users describe a project/task and need matching experts

#### Response Format:
All methods with `_with_reasoning` suffix return both the result and the reasoning trace for transparency.

## Usage Example

Here's a complete example combining all tools:

```python
import asyncio
from tools.elasticsearch_client import ElasticsearchClient
from tools.embedding_generator import EmbeddingGenerator
from tools.llm_client import LLMClient

async def find_experts(user_query: str):
    # Initialize tools
    es_client = ElasticsearchClient()
    embedding_gen = EmbeddingGenerator()
    llm_client = LLMClient()
    
    # Analyze query intent
    analysis, reasoning = await llm_client.analyze_query_with_reasoning(user_query)
    print(f"Analysis reasoning: {reasoning}")
    
    # Extract keywords
    keywords, _ = await llm_client.extract_keywords_with_reasoning(user_query)
    
    # Generate embedding
    query_embedding = embedding_gen.generate_embedding(user_query)
    
    # Perform hybrid search
    results = es_client.hybrid_search(
        index="experts",
        embedding_field="embedding",
        query_embedding=query_embedding,
        text_fields=["bio", "headline", "skills"],
        keywords=keywords,
        size=20
    )
    
    # Rerank results
    final_results, _ = await llm_client.rerank_with_reasoning(user_query, results)
    
    return final_results

# Run the search
results = asyncio.run(find_experts("Looking for a senior ML engineer"))
```



