# Multi-Format Ingestion & Document Modeling

## 1. Ingestion Pipeline (`backend/app/services/ingestion/`)

- **`FileDetector` (`detectors.py`)**: Identifies CSV, TSV, JSON, JSONL, Excel (`.xlsx`), Parquet (`.parquet`), PDF, Markdown, TXT, and legacy SQL/SQLite files.
- **`FormatConverter` (`converters.py`)**:
  - Sanitizes collection and field names (stripping null bytes and leading `$` operators).
  - Applies `_structure_mongo_document()` to automatically group prefixed attributes (`contact_*`, `address_*`, `location_*`, `shipping_*`, `billing_*`) and dot-separated headers into nested BSON sub-documents.
  - Parses JSON array/object columns into native MongoDB lists and dicts.
  - Calls `_create_intelligent_indexes()` to index `id`, `*_id`, `email`, `status`, `category`, `department`, `month`, and `date` fields.
