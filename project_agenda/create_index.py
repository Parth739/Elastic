from elasticsearch import Elasticsearch
import json

def create_project_agenda_index(es_host='http://localhost:9200', index_name='project_agendas'):
    """
    Elasticsearch index for project agenda data with support for
    keyword search and vector embeddings on agenda questions/responses
    """
    
    # Elasticsearch client
    es = Elasticsearch([es_host])
    
    # Index configuration
    index_config = {
        "settings": {
            "number_of_shards": 3,
            "number_of_replicas": 1,
            "analysis": {
                "analyzer": {
                    "agenda_analyzer": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": [
                            "lowercase",
                            "stop",
                            "snowball"
                        ]
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                # Project fields
                "project_id": {"type": "integer"},
                "topic": {
                    "type": "text",
                    "analyzer": "agenda_analyzer",
                    "fields": {
                        "keyword": {"type": "keyword"}
                    }
                },
                "external_topic": {
                    "type": "text",
                    "analyzer": "agenda_analyzer"
                },
                "client_id": {"type": "integer"},
                "client_name": {"type": "keyword"},
                "client_geography": {"type": "keyword"},
                "expert_geographies": {"type": "keyword"},
                "account_manager": {"type": "keyword"},
                "research_analysts": {"type": "keyword"},
                "case_code": {"type": "keyword"},
                "priority": {"type": "keyword"},
                "status": {"type": "keyword"},
                "type": {"type": "keyword"},
                "category": {"type": "keyword"},
                "no_of_calls": {"type": "integer"},
                "call_count": {"type": "integer"},
                "total_revenue": {"type": "float"},
                "description": {
                    "type": "text",
                    "analyzer": "agenda_analyzer"
                },
                "target_companies": {
                    "type": "text",
                    "analyzer": "agenda_analyzer"
                },
                "archetypes": {
                    "type": "text",
                    "analyzer": "agenda_analyzer"
                },
                "offlimit_topics": {
                    "type": "text",
                    "analyzer": "agenda_analyzer"
                },
                "offlimit_companies": {
                    "type": "text",
                    "analyzer": "agenda_analyzer"
                },
                "domains": {
                    "properties": {
                        "l0": {"type": "keyword"},
                        "l1": {"type": "keyword"},
                        "l2": {"type": "keyword"},
                        "l3": {"type": "keyword"},
                        "others": {
                            "type": "text",
                            "analyzer": "agenda_analyzer"
                        }
                    }
                },
                "functions": {
                    "type": "text",
                    "analyzer": "agenda_analyzer",
                    "fields": {
                        "keyword": {"type": "keyword"}
                    }
                },
                "receiving_date": {"type": "date"},
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
                "target_date": {"type": "date"},
                
                # Agenda specific fields
                "applicable_agenda_id": {"type": "integer"},
                "agenda_questions": {
                    "type": "nested",
                    "properties": {
                        "question_id": {"type": "keyword"},
                        "question_text": {
                            "type": "text",
                            "analyzer": "agenda_analyzer"
                        },
                        "question_type": {"type": "keyword"},
                        "required": {"type": "boolean"},
                        "order": {"type": "integer"}
                    }
                },
                
                # Expert responses 
                "expert_responses": {
                    "type": "nested",
                    "properties": {
                        "pe_agenda_id": {"type": "integer"},
                        "expert_id": {"type": "integer"},
                        "expert_name": {"type": "keyword"},
                        "expert_headline": {
                            "type": "text",
                            "analyzer": "agenda_analyzer"
                        },
                        "expert_location": {"type": "keyword"},
                        "expert_functions": {"type": "keyword"},
                        "expert_domains": {"type": "keyword"},
                        "years_of_experience": {"type": "integer"},
                        "relevant_company": {"type": "keyword"},
                        "relevant_designation": {
                            "type": "text",
                            "fields": {
                                "keyword": {"type": "keyword"}
                            }
                        },
                        "relevant_division": {"type": "keyword"},
                        "agenda_status": {"type": "keyword"},
                        "expert_invitation": {"type": "keyword"},
                        "state": {"type": "keyword"},
                        "shared_on": {"type": "date"},
                        "responded_on": {"type": "date"},
                        "responses": {
                            "type": "nested",
                            "properties": {
                                "question_id": {"type": "keyword"},
                                "question_text": {
                                    "type": "text",
                                    "analyzer": "agenda_analyzer"
                                },
                                "answer": {
                                    "type": "text",
                                    "analyzer": "agenda_analyzer"
                                },
                                "answer_embedding": {
                                    "type": "dense_vector",
                                    "dims": 768,
                                    "index": True,
                                    "similarity": "cosine"
                                }
                            }
                        },
                        "combined_qa_text": {
                            "type": "text",
                            "analyzer": "agenda_analyzer"
                        },
                        "combined_qa_embedding": {
                            "type": "dense_vector",
                            "dims": 768,
                            "index": True,
                            "similarity": "cosine"
                        }
                    }
                },
                
                # Project-level embeddings
                "project_description_embedding": {
                    "type": "dense_vector",
                    "dims": 768,
                    "index": True,
                    "similarity": "cosine"
                },
                "agenda_questions_embedding": {
                    "type": "dense_vector",
                    "dims": 768,
                    "index": True,
                    "similarity": "cosine"
                },
                "combined_project_embedding": {
                    "type": "dense_vector",
                    "dims": 768,
                    "index": True,
                    "similarity": "cosine"
                }
            }
        }
    }
    
    try:
        # Check if index already exists
        if es.indices.exists(index=index_name):
            print(f"Index '{index_name}' already exists. Deleting...")
            es.indices.delete(index=index_name)
            print(f"Index '{index_name}' deleted.")
        
        # Create new index
        response = es.indices.create(index=index_name, body=index_config)
        print(f"Index '{index_name}' created successfully!")
        
        # save configuration to file
        # with open(f'{index_name}_config.json', 'w') as f:
        #     json.dump(index_config, f, indent=2)
        # print(f"Index configuration saved to '{index_name}_config.json'")
        
        return response
        
    except Exception as e:
        print(f"Error creating index: {str(e)}")
        raise

if __name__ == "__main__":
    # Create index 
    create_project_agenda_index()
    
