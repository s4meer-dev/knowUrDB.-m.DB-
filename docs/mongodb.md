# MongoDB Data Modeling, Compass Folder Organization & System Collections

## 1. MongoDB Compass Folder Organization

To keep **MongoDB Compass** clean and easy to browse, `knowUrDB (m.DB)` isolates system metadata, the Demo dataset, and each uploaded dataset into dedicated MongoDB Database Folders:

```text
📁 knowurdb_demo              <-- Unified Demo Database Folder
 ├── 📄 customers             (50 docs — nested contact & address subdocuments)
 ├── 📄 employees             (60 docs — department, role, salary)
 ├── 📄 orders                (120 docs — embedded items[] arrays)
 ├── 📄 products              (12 docs — categories, prices, tags[])
 └── 📄 students              (100 docs — major, GPA, attendance)

📁 knowurdb_<dataset_name>    <-- Dedicated Folder per Uploaded File (e.g. knowurdb_brands)
 └── 📄 <collection_name>     (Clean collection name without prefixes, e.g. brands)

📁 knowurdb_system            <-- Internal Platform Registry & Vector RAG Store
 ├── 📄 _sys_collections_metadata
 ├── 📄 _sys_document_chunks
 ├── 📄 _sys_query_history
 ├── 📄 _sys_settings
 ├── 📄 _sys_sources
 └── 📄 _sys_workspaces
```

## 2. System Collections (`knowurdb_system` Database)

| Collection Name | Purpose | Indexed Keys |
| :--- | :--- | :--- |
| `_sys_workspaces` | Workspace configuration and active dataset tracking | `workspace_id` (unique) |
| `_sys_sources` | Registry of all uploaded datasets, `database_name` folder, collections, and schema summaries | `source_id` (unique), `uploaded_at` (-1), `status` (1) |
| `_sys_collections_metadata` | Per-collection document counts, index counts, `database_name`, and parent `source_id` | `(source_id, collection_name)` (unique) |
| `_sys_query_history` | Audit log of executed natural language queries, MongoDB pipelines, timings, and row counts | `id` (unique), `created_at` (-1) |
| `_sys_document_chunks` | Extracted text chunks and 128-dim L2-normalized vector embeddings for RAG | `chunk_id` (unique), `(source_id, page_number)` |
| `_sys_settings` | Runtime AI provider and workspace preferences | `key` (unique) |

## 3. Demo Dataset Document Modeling (`knowurdb_demo`)

`DemoGenerator` (`backend/app/services/demo_generator.py`) seeds 5 rich MongoDB collections inside `knowurdb_demo`:
- **`products`**: Product catalog with `category`, `price`, `stock`, `rating`, and embedded `tags[]` array.
- **`customers`**: Customer profiles with nested `contact` (`{"email": ..., "phone": ...}`) and `address` (`{"city": ..., "state": ..., "country": "India"}`) sub-documents, plus `total_spent` and `loyalty_tier`.
- **`orders`**: E-commerce orders with `customer_id`, `status`, `order_date`, `month`, `total_amount`, and an embedded `items[]` array (`[{"product_id": ..., "product_name": ..., "quantity": ..., "price": ..., "line_total": ...}]`).
- **`employees`**: Organization directory with `department`, `role`, `salary`, and `performance_score`.
- **`students`**: Academic records with `major`, `gpa`, `Attendance_Percentage`, and `credits_completed`.
