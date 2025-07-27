import os
from dotenv import load_dotenv
import urllib3

# Disable SSL warnings if needed
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

# Elasticsearch Configuration
ES_NODE = os.getenv("ES_NODE")
ES_USERNAME = os.getenv("ES_USERNAME")
ES_PASSWORD = os.getenv("ES_PASSWORD")
ES_VERIFY_CERTS = False

# Index Names
EXPERT_INDEX = "dynamic_expert_search_v1_0_12_with_embeddings"
PROJECT_INDEX = "dynamic_project_search_v1_0_6_with_embeddings_v1"

# LLM Configuration
LLM_API_URL = "https://llm-be.infollion.ai/api/generate"
LLM_MODEL = "deepseek-r1:32b-qwen-distill-q4_K_M" 
LLM_TIMEOUT = 120

# Embedding Model
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

# Configuration
MAX_SEARCH_ITERATIONS = 10
TARGET_QUALITY_SCORE = 0.9
BACKGROUND_MONITOR_INTERVAL = 1800  # 30 minutes
LEARNING_RATE = 0.1

# Storage Paths
DATA_PATH = "data"
LEARNING_STORAGE_PATH = os.path.join(DATA_PATH, "learning")
SESSION_STORAGE_PATH = os.path.join(DATA_PATH, "sessions")
FEEDBACK_STORAGE_PATH = os.path.join(DATA_PATH, "feedback")
