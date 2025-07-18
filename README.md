# Elastic Setup

##  Structure

```
.
├── expert_data/
│   ├── create_index.py      # Creates Elasticsearch index schema for experts
│   └── indexing.py          # Fetches MySQL data and indexes experts with embeddings
│
├── project_agenda/
│   ├── create_index.py      # Creates Elasticsearch index schema for projects
│   └── indexing.py          # Fetches MySQL data and indexes projects with Q&A embedding
```

---
