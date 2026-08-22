# Phase 3: Natural Language to SQL Engine

Phase 3 introduces the first fully working query engine for knowUrDB. To maintain absolute safety and stability, this phase uses a deterministic translation pipeline instead of an external LLM. It maps natural language questions about the schema into an intermediate query plan, which is then safely built into SQL.

## Architecture

```
Question Input
      ↓
Normalization (lowercase, remove punctuation)
      ↓
Intent & Entity Extraction (Pattern matching based on Phase 2 Benchmarks)
      ↓
Query Plan (intent, entity, metrics, filters)
      ↓
SQL Builder (assembles SELECT... FROM... WHERE...)
      ↓
SQL Safety Validator (Rejects non-SELECT queries)
      ↓
Query Executor (Reads from Read-Only DB, returns columns & rows)
```

## Features
- **Schema Intelligence Layer**: Reads `PRAGMA` to get tables, columns, and relations.
- **SQL Validator**: Strict safety layer blocking `INSERT`, `UPDATE`, `DROP`, multiple statements, etc.
- **API Endpoint**: `POST /api/query` returns structured rows and metadata.
- **Frontend UI**: Integrated chat-style interface, suggestions, data table display, and collapsible SQL viewer.

## Supported Capabilities
The pipeline currently supports concepts from the Phase 2 benchmark evaluation:
- Counting entities (e.g., `COUNT(*)`)
- Filtering by simple equality or inequality.
- Custom benchmark queries (e.g., joins, window functions, CTEs) via semantic matching.

## Future LLM Integration Points
The `text_to_sql_service.py` is modular. In future phases, the deterministic `create_query_plan` logic can be swapped or augmented with an LLM that translates unknown natural language questions into the same `QueryPlan` structure, or directly to SQL that is then validated by `SQLValidator`.
