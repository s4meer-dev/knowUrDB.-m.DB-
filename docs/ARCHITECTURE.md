# knowUrDB (m.DB) — System Architecture

## 1. High-Level Overview

`knowUrDB (m.DB)` is architected from the ground up around **MongoDB** as its unified persistence, analytics, metadata, and vector retrieval engine.

### Core Layers
1. **Presentation Layer (`frontend/`)**:
   - Built with React 19, TypeScript, Tailwind CSS v4, and Recharts.
   - Displays interactive MongoDB Aggregation Pipelines (`MongoQueryPanel` with stage badges `$match`, `$group`, `$lookup`, `$unwind`, `$sort`, `$limit`), BSON field paths (`contact.email`, `items[].price`), collection indexes, and sample JSON documents.
2. **Orchestration & Routing Layer (`backend/app/api/`, `backend/app/services/query_router.py`)**:
   - Classifies every natural-language request into one of five execution paths:
     - `META`: Workspace-level catalog introspection (`_sys_sources`, `_sys_collections_metadata`).
     - `SINGLE_SOURCE`: Targets a specific MongoDB dataset and executes an aggregation or find pipeline.
     - `CLARIFICATION_REQUIRED`: Triggered when multiple MongoDB sources score within the ambiguity threshold.
     - `COMPARISON`: Executes parallel MongoDB pipelines across multiple datasets and synthesizes deltas.
     - `DOCUMENT_RAG`: Performs hybrid vector + lexical search over `_sys_document_chunks`.
3. **MongoDB Data & Storage Layer (`backend/app/core/mongodb.py`)**:
   - Managed by `MongoDBManager` with connection pooling (`maxPoolSize=50`), automatic health checks (`ping`), and seamless fallback to `mongomock` when running in isolated CI containers without a local daemon.
