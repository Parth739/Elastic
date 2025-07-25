## Index Creation and Data Ingestion

- `create_index.py` and `indexing_files.py` are general-purpose scripts used to:
  - Create Elasticsearch indices with custom mappings.
  - Ingest structured data with all necessary fields.

---

## `indexing_expert_data_with_embeddings.py` — Reindexing with Embeddings

This script reindexes existing expert data into a new index that supports **semantic search** using vector embeddings.

- Initially, all `work_experience` entries were stored as a **single concatenated text field**.
- This approach **reduced semantic accuracy**, as diverse experiences blended together confused embedding models and degraded retrieval quality.

### Improved Structure

- Each `work_experience` is now stored as a **nested document**.
- An **individual embedding** is generated for each experience, enabling:
  - Better semantic granularity.
  - More relevant and precise search results.

### Trade-offs

- **Pros:**
  - Significantly improved semantic retrieval.
  - Fine-grained search based on specific work experiences.

- **Cons:**
  - Increased indexing time due to more embeddings.
  - Higher search latency from nested structure and larger vector space.

---
