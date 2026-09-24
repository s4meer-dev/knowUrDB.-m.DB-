# Testing & Verification Suite

## 1. Backend Pytest Suite (`51/51 Passed`)

Run from `backend/`:
```bash
python -m pytest -v
```

### Test Modules
- `tests/test_mongodb_native_suite.py`:
  - `test_01_mongodb_connection_and_ping`: Verifies live MongoDB health & demo collection seeding.
  - `test_02_csv_ingestion_with_nested_document_modeling`: Verifies CSV upload creates nested `contact` and `address` BSON sub-documents and executes aggregation pipelines.
  - `test_03_json_ingestion`: Verifies native JSON array/object ingestion and querying.
  - `test_04_excel_ingestion`: Verifies `.xlsx` multi-row ingestion into MongoDB.
  - `test_05_parquet_ingestion`: Verifies `.parquet` columnar ingestion into MongoDB.
  - `test_06_pdf_and_markdown_rag_ingestion_and_retrieval`: Verifies Markdown/PDF upload, vector embedding storage in `_sys_document_chunks`, and hybrid RAG retrieval.
  - `test_07_clarification_flow_for_ambiguous_sources`: Verifies `clarification_required` routing when multiple similar datasets exist.
  - `test_08_multi_source_comparison_flow`: Verifies cross-source MongoDB aggregation comparison.
  - `test_09_comprehensive_mongodb_security_validator` (10 parametrized payloads): Verifies rejection of `deleteMany`, `drop`, `$out`, `$merge`, `$where`, `$function`, `_sys_sources` access, and `$lookup` privilege escalation.
- `tests/api/test_query.py`: Natural language aggregation queries (`$count`, `$unwind` + `$group` top products by revenue, `$match` customers over ₹1 lakh, month-over-month sales comparison, average salary by department).
- `tests/api/test_schema.py`: Collection introspection, BSON field paths, and system collection blocking.
- `tests/api/test_upload.py` & `tests/test_ingestion_locks.py`: Single, batch, duplicate-filename, and concurrent MongoDB uploads.
- `tests/api/test_history.py`, `tests/api/test_suggestions.py`, `tests/api/test_ai_api.py`, `tests/test_health.py`.

## 2. Frontend Test & Build Suite (`6/6 Passed`)

Run from `frontend/`:
```bash
npm run test
npm run lint
npm run build
```
