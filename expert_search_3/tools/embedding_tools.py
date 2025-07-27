from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List
from config.settings import EMBEDDING_MODEL
import logging

logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    def __init__(self):
        try:
            self.model = SentenceTransformer(EMBEDDING_MODEL)
            logger.info(f"Loaded embedding model: {EMBEDDING_MODEL}")
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        try:
            embedding = self.model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * 384
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        try:
            embeddings = self.model.encode(texts)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            # Return zero vectors as fallback
            return [[0.0] * 384 for _ in texts]
    
    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Compute cosine similarity between two embeddings"""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            cosine_sim = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
            return float(cosine_sim)
        except Exception as e:
            logger.error(f"Error computing similarity: {e}")
            return 0.0
