# AI Expert Search

## Functions

- **Intelligent Query Understanding**: Uses LLMs to analyze user intent and extract requirements
- **Hybrid Search**: Combines semantic embeddings and keyword matching for optimal results
- **Workflow Orchestration**: State-based workflows with automatic retry and quality checks
- **Session Management**: Maintains conversation context for personalized experiences
- **Feedback Learning**: Collects user satisfaction data to improve recommendations over time
- **Transparent Reasoning**: Provides detailed reasoning traces for all AI decisions


### Prerequisites

- Python 3.9+
- Elasticsearch 7.x or 8.x
- Access to an LLM API (OpenAI, Anthropic, etc.)

### Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ai-expert-search.git
   cd ai-expert-search
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up configuration**
   ```bash
   cp config/settings.example.py config/settings.py
   # Edit config/settings.py with your credentials
   ```

5. **Initialize Elasticsearch indices**
   ```bash
   python scripts/init_elasticsearch.py
   ```

## ⚙️ Configuration

Edit `config/settings.py` with your credentials and preferences:

```python
# Elasticsearch Configuration
ES_NODE = "https://your-elasticsearch-url:9200"
ES_USERNAME = "your-username"
ES_PASSWORD = "your-password"
ES_VERIFY_CERTS = True
EXPERT_INDEX = "experts"
PROJECT_INDEX = "projects"

# Embedding Model Configuration
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

# LLM Configuration
LLM_API_URL = "https://api.openai.com/v1/chat/completions"
LLM_MODEL = "gpt-4"
LLM_API_KEY = "your-api-key"
LLM_TIMEOUT = 30.0

# Storage Configuration
SESSION_STORAGE_PATH = "data/sessions"
FEEDBACK_STORAGE_PATH = "data/feedback"

# Search Configuration
DEFAULT_SEARCH_SIZE = 10
MAX_SEARCH_SIZE = 50
```

## Quick Start

### Running the Application

```bash
# Start the FastAPI server
python main.py
```

The API will be available at `http://localhost:8000`

### Basic Usage

```python
import asyncio
from workflows.expert_search_workflow import ExpertSearchWorkflow

async def find_experts():
    workflow = ExpertSearchWorkflow()
    
    # Search for experts
    result = await workflow.run("I need a machine learning expert for computer vision")
    
    # Access results
    experts = result["experts"]
    for expert in experts:
        print(f"{expert.name} - {expert.headline} (Score: {expert.score})")

# Run the search
asyncio.run(find_experts())
```

## Components

### 1. **Agents** (`/agents`)
Intelligent processing units that handle specific tasks:
- **QueryAnalyzer**: Understands user intent and structures queries
- **SearchAgent**: Executes search strategies against Elasticsearch
- **Reranker**: Optimizes result ordering based on relevance
- **QueryEnhancer**: Improves queries for better results

### 2. **Workflows** (`/workflows`)
Orchestrates agents using state machines:
- **ExpertSearchWorkflow**: Main workflow for expert search
- **AutonomousWorkflow**: Extended workflow with advanced capabilities

### 3. **Tools** (`/tools`)
Core utilities for system functionality:
- **ElasticsearchClient**: Handles all search operations
- **EmbeddingGenerator**: Creates vector representations
- **LLMClient**: Interfaces with language models

### 4. **Utils** (`/utils`)
Supporting utilities:
- **SessionManager**: Maintains conversation context
- **FeedbackManager**: Collects and analyzes user feedback

### 5. **Models** (`/models`)
Data structures and schemas:
- **Expert**: Expert profile representation
- **SearchQuery**: Structured query format
- **WorkflowState**: Workflow state management

### 6. **Config** (`/config`)
System configuration and settings

### 7. **Storage** (`/storage`)
Data persistence layer for sessions and feedback

## Usage Examples

### 1. Direct Expert Search

```python
# Search for specific expertise
result = await workflow.run("Looking for a senior Python developer with Django experience")
```

### 2. Project-Based Search

```python
# Describe your project to find matching experts
result = await workflow.run(
    "I'm building a recommendation system using deep learning and need "
    "someone to help with model architecture and deployment"
)
```

### 3. Session-Based Search

```python
from utils.session_manager import SessionManager

session_mgr = SessionManager()
session_id = session_mgr.create_session()

# First search
result1 = await workflow.run("Find ML expert", session_id=session_id)

# Follow-up search uses context
result2 = await workflow.run("Only those available for remote work", session_id=session_id)
```

## Improvements Needed

1. **Fine-tuning an embedding model for expert profile generation**  
   Instead of directly querying the expert DB, we can first fine-tune a model to generate an "ideal expert profile" from the project agenda. This generated profile (a sort of target vector) can then be used for vector similarity search, significantly improving semantic relevance.

2. **Fine-tuning a reranker model**  
   The current reranking approach uses LLMs like DeepSeek/Qwen with 30–35 experts, which consumes time and exceeds context window limitations. Fine-tuning a lightweight reranker (e.g., monoBERT or cohere-rerank) will allow us to pre-rank top candidates efficiently. Then, deeper LLM-based reasoning can be applied on the smaller, high-quality result set.

3. **Adding confidence scores with explanations**  
   Every expert suggestion should come with a confidence score and a short rationale (e.g., “matched on NLP, GenAI, past healthcare projects”), which can be generated from metadata or using shallow LLM inference. This improves transparency and user trust.

4. Make all indexing and search operations concurrent where applicable (e.g., indexing multiple expert profiles or processing multiple agenda embeddings) to optimize performance.

5. **Interactive follow-up agent loop**  
   Enable multi-turn interaction where the agent can ask clarification questions (e.g., “Should the expert have startup experience?”) before finalizing the recommendation.






