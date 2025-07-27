##  Structure

```
.
├── Basic_Implementation_without_langgraph/   
├── Deploying LLM using Ollama/              
├── Fine_Tunning/                            
├── Langgraph/                              
├── expert_data/                             
├── expert_search_3/                       
├── expert_search_langgraph/                
├── project_agenda/                          
└── README.md                                
```

## Components

### Basic Implementation without LangGraph
A straightforward implementation of LLM functionality without the complexity of LangGraph. Without any graph-based flows, this was developed first to test basic working, LLM integration, and function creation. **Perfect for understanding core LLM interaction patterns** before moving to advanced architectures.

**Features:**
- Direct LLM API integration
- Simple prompt engineering
- Basic response handling
- Function calling demonstrations

### Deploying LLM using Ollama
Step-by-step process to deploy LLM on GPU servers or local machines using Ollama - the simplest way to run open-source models like **Llama 2 locally** Also includes setting up HTTPS API using nginx for secure remote access.

**What's Included:**
- Ollama installation guide
- Model selection and downloading
- API endpoint configuration
- Nginx reverse proxy setup
- Security best practices

### Fine-Tuning Module
Fine-tuning of Llama models on Kaggle using the project agenda dataset. The effectiveness of fine-tuning depends heavily on how the custom dataset is shaped according to input and output requirements. This module demonstrates **structured output generation** for domain-specific tasks.

**Contents:**
- Dataset preparation scripts
- Fine-tuning notebooks
- Hyperparameter configurations
- Evaluation metrics
- Model deployment guides

### LangGraph
Learn LangGraph basics including graph creation, LLM integration, state flow management, and building basic ReAct agents. **LangGraph enables building stateful, multi-actor applications** with features like:

- **Cycles**: Support for iterative processes
- **Controllability**: Fine-grained control over execution flow
- **Persistence**: State management across conversations

### Expert Search Systems

#### expert_search_3
Third iteration of the expert search system featuring:
- Optimized search algorithms
- Enhanced relevance scoring
- Multi-source integration
- Performance improvements

ALL Useful links - 

TLDraw - https://www.tldraw.com/f/FKrF5S80z5kSVhfXNWcyl?d=v-4416.-5739.5845.3232.Azw61EZF58rPBasK0naA2
Articles 
- https://dassum.medium.com/fine-tune-large-language-model-llm-on-a-custom-dataset-with-qlora-fb60abdeba07
- https://www.datacamp.com/tutorial/fine-tuning-large-language-models
- https://medium.com/data-science/from-basics-to-advanced-exploring-langgraph-e8c1cf4db787
- https://www.pinecone.io/learn/langgraph-research-agent/
- https://blog.futuresmart.ai/multi-agent-system-with-langgraph
- https://vijaykumarkartha.medium.com/multiple-ai-agents-creating-multi-agent-workflows-using-langgraph-and-langchain-0587406ec4e6

