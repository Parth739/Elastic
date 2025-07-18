import json
from elasticsearch import Elasticsearch

expert_index_config = {
    "settings": {
        "number_of_shards": 3,  
        "number_of_replicas": 1,
        "analysis": {
            "tokenizer": {
                "standard": {
                    "type": "standard"
                }
            },
            "filter": {
                "stopwords_filter": {
                    "type": "stop",
                    "stopwords": "_english_"
                },
                "lowercase_filter": {
                    "type": "lowercase"
                },
                "punctuation_filter": {
                    "type": "pattern_replace",
                    "pattern": "[\\p{P}]",
                    "replacement": ""
                }
            },
            "analyzer": {
                "custom_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": [
                        "lowercase_filter",
                        "stopwords_filter",
                        "punctuation_filter"
                    ]
                }
            },
            "normalizer": {
                "clean_normalizer": {
                    "type": "custom",
                    "filter": [
                        "lowercase_filter",
                        "punctuation_filter"
                    ]
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "id": {"type": "integer"},
            "name": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "normalizer": "clean_normalizer"
                    }
                },
                "analyzer": "custom_analyzer"
            },
            "type": {
                "type": "keyword",
                "normalizer": "clean_normalizer"
            },
            "badge": {
                "type": "keyword",
                "normalizer": "clean_normalizer"
            },
            "source_link": {"type": "keyword"},
            "status": {
                "type": "keyword",
                "normalizer": "clean_normalizer"
            },
            "private_profile": {"type": "boolean"},
            "dnd_enabled": {"type": "boolean"},
            "premium_expert": {"type": "boolean"},
            "base_location": {
                "type": "keyword",
                "normalizer": "clean_normalizer"
            },
            "fk_project": {"type": "integer"},
            "is_self_registered": {"type": "boolean"},
            "user_id": {"type": "integer"},
            "primary_mobile": {
                "type": "text",
                "analyzer": "custom_analyzer",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "normalizer": "clean_normalizer"
                    }
                }
            },
            "all_mobile_numbers": {
                "type": "text",
                "analyzer": "custom_analyzer",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "normalizer": "clean_normalizer"
                    }
                }
            },
            "headline": {
                "type": "text",
                "analyzer": "custom_analyzer"
            },
            "functions": {
                "type": "text",
                "analyzer": "custom_analyzer",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "normalizer": "clean_normalizer"
                    }
                }
            },
            "picture": {
                "type": "keyword",
                "index": False
            },
            "bio": {
                "type": "text",
                "analyzer": "custom_analyzer"
            },
            "internal_notes": {
                "type": "text",
                "analyzer": "custom_analyzer"
            },
            "expertise_in_these_geographies": {
                "type": "keyword",
                "normalizer": "clean_normalizer"
            },
            "primary_email": {
                "type": "keyword",
                "normalizer": "clean_normalizer"
            },
            "all_emails": {
                "type": "text",
                "analyzer": "custom_analyzer",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "normalizer": "clean_normalizer"
                    }
                }
            },
            "fk_creator": {
                "type": "keyword",
                "normalizer": "clean_normalizer"
            },
            "updated_by": {
                "type": "keyword",
                "normalizer": "clean_normalizer"
            },
            "approved_by": {
                "type": "keyword",
                "normalizer": "clean_normalizer"
            },
            "domain_l0": {
                "type": "keyword",
                "normalizer": "clean_normalizer"
            },
            "domain_l1": {
                "type": "keyword",
                "normalizer": "clean_normalizer"
            },
            "domain_l2": {
                "type": "keyword",
                "normalizer": "clean_normalizer"
            },
            "domain_l3": {
                "type": "keyword",
                "normalizer": "clean_normalizer"
            },
            "domain_other": {
                "type": "text",
                "analyzer": "custom_analyzer",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "normalizer": "clean_normalizer"
                    }
                }
            },
            "offlimit_topics": {
                "type": "text",
                "analyzer": "custom_analyzer"
            },
            "offlimit_companies": {
                "type": "text",
                "analyzer": "custom_analyzer"
            },
            "created_at": {
                "type": "date",
                "format": "yyyy-MM-dd"
            },
            "updated_at": {
                "type": "date",
                "format": "yyyy-MM-dd"
            },
            "confirmed_on": {
                "type": "date",
                "format": "yyyy-MM-dd"
            },
            "call_count": {"type": "integer"},
            "pending_edits": {"type": "integer"},
            "total_years_of_experience": {"type": "integer"},
            "work_experiences": {
                "type": "nested",
                "properties": {
                    "id": {"type": "integer"},
                    "company": {
                        "type": "text",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "normalizer": "clean_normalizer"
                            }
                        },
                        "analyzer": "custom_analyzer"
                    },
                    "fk_company": {"type": "integer"},
                    "status": {
                        "type": "keyword",
                        "normalizer": "clean_normalizer"
                    },
                    "designation": {
                        "type": "text",
                        "analyzer": "custom_analyzer",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "normalizer": "clean_normalizer"
                            }
                        }
                    },
                    "division": {
                        "type": "text",
                        "analyzer": "custom_analyzer",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "normalizer": "clean_normalizer"
                            }
                        }
                    },
                    "job_description": {
                        "type": "text",
                        "analyzer": "custom_analyzer"
                    },
                    "country": {
                        "type": "text",
                        "analyzer": "custom_analyzer",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "normalizer": "clean_normalizer"
                            }
                        }
                    },
                    "location": {
                        "type": "text",
                        "analyzer": "custom_analyzer",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "normalizer": "clean_normalizer"
                            }
                        }
                    },
                    "start_date": {
                        "type": "date",
                        "format": "yyyy-MM-dd"
                    },
                    "end_date": {
                        "type": "date",
                        "format": "yyyy-MM-dd"
                    },
                    "currently_works_here": {"type": "boolean"}
                }
            },
            "awards": {
                "type": "object",
                "properties": {
                    "date": {"type": "keyword"},
                    "title": {"type": "text"},
                    "description": {
                        "type": "text",
                        "analyzer": "custom_analyzer"
                    }
                }
            },
            "patents": {
                "type": "object",
                "properties": {
                    "date": {"type": "keyword"},
                    "title": {"type": "text"},
                    "number": {"type": "keyword"},
                    "patent_url": {"type": "keyword"},
                    "description": {
                        "type": "text",
                        "analyzer": "custom_analyzer"
                    }
                }
            },
            "snippets": {
                "type": "object",
                "properties": {
                    "heading": {"type": "text"},
                    "description": {
                        "type": "text",
                        "analyzer": "custom_analyzer"
                    }
                }
            },
            "education": {
                "type": "object",
                "properties": {
                    "course": {
                        "type": "text",
                        "analyzer": "custom_analyzer"
                    },
                    "start_year": {"type": "keyword"},
                    "end_year": {"type": "keyword"},
                    "institution": {
                        "type": "text",
                        "analyzer": "custom_analyzer"
                    }
                }
            },
            "webhandles": {
                "type": "object",
                "properties": {
                    "link": {"type": "keyword"},
                    "portal": {
                        "type": "keyword",
                        "normalizer": "clean_normalizer"
                    }
                }
            },
            "publications": {
                "type": "object",
                "properties": {
                    "date": {"type": "keyword"},
                    "title": {"type": "text"},
                    "description": {
                        "type": "text",
                        "analyzer": "custom_analyzer"
                    },
                    "publication": {"type": "text"},
                    "description_url": {"type": "keyword"}
                }
            },

            # Vector embeddings for different features
            "combined_embedding": {
                "type": "dense_vector",
                "dims": 768,
                "index": True,
                "similarity": "cosine"
            },
            "bio_embedding": {
                "type": "dense_vector",
                "dims": 768,
                "index": True,
                "similarity": "cosine"
            },
            "headline_embedding": {
                "type": "dense_vector",
                "dims": 768,
                "index": True,
                "similarity": "cosine"
            },
            "work_experience_embedding": {
                "type": "dense_vector",
                "dims": 768,
                "index": True,
                "similarity": "cosine"
            }
        }
    }
}

# indexing funcntion
def create_expert_index(es_host='http://localhost:9200', index_name='experts_data_index'):
    es = Elasticsearch([es_host])
    
    # Delete existing index if it exists
    if es.indices.exists(index=index_name):
        print(f"Deleting existing index: {index_name}")
        es.indices.delete(index=index_name)
    
    # Create new index
    response = es.indices.create(index=index_name, body=expert_index_config)
    print(f"Index '{index_name}' created successfully!")
    return response

# Save config to file
with open('expert_index_config.json', 'w') as f:
    json.dump(expert_index_config, f, indent=2)

if __name__ == "__main__":
    create_expert_index()
