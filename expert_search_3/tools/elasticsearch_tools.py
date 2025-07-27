from elasticsearch import Elasticsearch
from typing import List, Dict, Any, Union
import numpy as np
import re
from config.settings import ES_NODE, ES_USERNAME, ES_PASSWORD, EXPERT_INDEX, PROJECT_INDEX, ES_VERIFY_CERTS
import logging
import json

logger = logging.getLogger(__name__)

class ElasticsearchClient:
    def __init__(self):
        try:
            self.client = Elasticsearch(
                [ES_NODE],
                basic_auth=(ES_USERNAME, ES_PASSWORD),
                verify_certs=ES_VERIFY_CERTS,
                ssl_show_warn=False
            )
            if not self.client.ping():
                logger.error("Failed to connect to Elasticsearch")
                raise ConnectionError("Cannot connect to Elasticsearch")
        except Exception as e:
            logger.error(f"Error initializing Elasticsearch client: {e}")
            raise
    
    def semantic_search(self, index: str, embedding_field: str, 
                       query_embedding: List[float], size: int = 10) -> List[Dict]:
        """Perform semantic search using knn search"""
        try:
            query = {
                "size": size,
                "knn": {
                    "field": embedding_field,
                    "query_vector": query_embedding,
                    "k": size,
                    "num_candidates": size * 2
                },
                "_source": True
            }
            
            try:
                response = self.client.search(index=index, body=query)
                return [hit for hit in response["hits"]["hits"]]
            except:
                query = {
                    "size": size,
                    "query": {
                        "script_score": {
                            "query": {"match_all": {}},
                            "script": {
                                "source": """
                                    double value = dotProduct(params.query_vector, doc[params.field]);
                                    return sigmoid(1, Math.E, -value);
                                """,
                                "params": {
                                    "field": embedding_field,
                                    "query_vector": query_embedding
                                }
                            }
                        }
                    },
                    "_source": True
                }
                
                response = self.client.search(index=index, body=query)
                return [hit for hit in response["hits"]["hits"]]
                
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return []
    
    def keyword_search(self, index: str, fields: List[str], 
                      keywords: List[str], size: int = 10) -> List[Dict]:
        """Perform keyword search across multiple fields"""
        try:
            cleaned_keywords = []
            for keyword in keywords:
                cleaned = re.sub(r'[^\w\s-]', '', str(keyword)).strip()
                if cleaned and len(cleaned) > 1:
                    cleaned_keywords.append(cleaned)
            
            if not cleaned_keywords:
                logger.warning("No valid keywords after cleaning")
                return []
            
            should_clauses = []
            
            for keyword in cleaned_keywords[:10]:
                should_clauses.append({
                    "multi_match": {
                        "query": keyword,
                        "fields": fields,
                        "type": "best_fields",
                        "fuzziness": "AUTO"
                    }
                })
            
            if len(cleaned_keywords) > 1:
                should_clauses.append({
                    "multi_match": {
                        "query": " ".join(cleaned_keywords[:5]),
                        "fields": fields,
                        "type": "phrase",
                        "slop": 2
                    }
                })
            
            query = {
                "size": size,
                "query": {
                    "bool": {
                        "should": should_clauses,
                        "minimum_should_match": 1
                    }
                }
            }
            
            response = self.client.search(index=index, body=query)
            return [hit for hit in response["hits"]["hits"]]
            
        except Exception as e:
            logger.error(f"Keyword search error: {e}")
            try:
                simple_query = {
                    "size": size,
                    "query": {
                        "multi_match": {
                            "query": " ".join(keywords[:3]) if keywords else "expert",
                            "fields": fields if fields else ["description", "topic", "name"]
                        }
                    }
                }
                response = self.client.search(index=index, body=simple_query)
                return [hit for hit in response["hits"]["hits"]]
            except Exception as fallback_error:
                logger.error(f"Fallback search also failed: {fallback_error}")
                return []
    
    def hybrid_search(self, index: str, embedding_field: str, 
                     query_embedding: List[float], text_fields: List[str],
                     keywords: List[str], size: int = 10) -> List[Dict]:
        """Combined semantic and keyword search"""
        try:
            keyword_results = self.keyword_search(index, text_fields, keywords, size * 2)
            
            semantic_results = []
            if query_embedding:
                semantic_results = self.semantic_search(index, embedding_field, query_embedding, size)
            
            combined_results = {}
            
            for hit in keyword_results:
                doc_id = hit["_id"]
                combined_results[doc_id] = {
                    "hit": hit,
                    "score": hit.get("_score", 0) * 1.2
                }
            
            for hit in semantic_results:
                doc_id = hit["_id"]
                if doc_id in combined_results:
                    combined_results[doc_id]["score"] += hit.get("_score", 0) * 1.5
                else:
                    combined_results[doc_id] = {
                        "hit": hit,
                        "score": hit.get("_score", 0) * 1.5
                    }
            
            sorted_results = sorted(
                combined_results.values(), 
                key=lambda x: x["score"], 
                reverse=True
            )[:size]
            
            return [result["hit"] for result in sorted_results]
            
        except Exception as e:
            logger.error(f"Hybrid search error: {e}")
            return self.keyword_search(index, text_fields, keywords, size)
    
    def get_by_ids(self, index: str, ids: List[int]) -> List[Dict]:
        """Get documents by IDs"""
        try:
            if not ids:
                return []
            
            query = {
                "query": {
                    "terms": {"id": ids}
                }
            }
            response = self.client.search(index=index, body=query, size=len(ids))
            return [hit for hit in response["hits"]["hits"]]
        except Exception as e:
            logger.error(f"Get by IDs error: {e}")
            return []
    
    def get_recent_documents(self, index: str, field: str = "@timestamp", 
                           size: int = 100) -> List[Dict]:
        """Get recent documents from index"""
        try:
            query = {
                "size": size,
                "sort": [{field: {"order": "desc"}}],
                "query": {"match_all": {}}
            }
            response = self.client.search(index=index, body=query)
            return [hit for hit in response["hits"]["hits"]]
        except:
            # Fallback without timestamp
            query = {
                "size": size,
                "query": {"match_all": {}}
            }
            response = self.client.search(index=index, body=query)
            return [hit for hit in response["hits"]["hits"]]
