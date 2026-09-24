# MongoDB Data Modeling & System Collections

## 1. System Collections (`knowurdb` Database)

| Collection Name | Purpose | Indexed Keys |
| :--- | :--- | :--- |
| `_sys_workspaces` | Workspace configuration and active dataset tracking | `workspace_id` (unique) |
| `_sys_sources` | Registry of all uploaded datasets, collections, status, and schema summaries | `source_id` (unique), `uploaded_at` (-1), `status` (1) |
| `_sys_collections_metadata` | Per-collection document counts, index counts, and parent `source_id` | `(source_id, collection_name)` (unique) |
| `_sys_query_history` | Audit log of executed natural language queries, MongoDB pipelines, timings, and row counts | `id` (unique), `created_at` (-1) |
| `_sys_document_chunks` | Extracted text chunks and 128-dim L2-normalized vector embeddings for RAG | `chunk_id` (unique), `(source_id, page_number)` |
| `_sys_settings` | Runtime AI provider and workspace preferences | `key` (unique) |

## 2. Demo Dataset Document Modeling

`DemoGenerator` (`backend/app/services/demo_generator.py`) seeds 5 rich MongoDB collections:
- **`products`**: Product catalog with `category`, `price`, `stock`, `rating`, and embedded `tags[]` array.
- **`customers`**: Customer profiles with nested `contact` (`{"email": ..., "phone": ...}`) and `address` (`{"city": ..., "state": ..., "country": "India"}`) sub-documents, plus `total_spent` and `loyalty_tier`.
- **`orders`**: E-commerce orders with `customer_id`, `status`, `order_date`, `month`, `total_amount`, and an embedded `items[]` array (`[{"product_id": ..., "product_name": ..., "quantity": ..., "price": ..., "line_total": ...}]`).
- **`employees`**: Organization directory with `department`, `role`, `salary`, and `performance_score`.
- **`students`**: Academic records with `major`, `gpa`, `Attendance_Percentage`, and `credits_completed`.
