# MongoDB Data Modeling, Compass Folder Organization & System Collections

## 1. Single-`knowurdb` MongoDB Compass Hierarchy

To ensure **MongoDB Compass** has **only ONE top-level database (`knowurdb`)** with zero scattered collections, `knowUrDB (m.DB)` organizes all data inside a single unified database tree:

```text
📁 knowurdb                         <-- Single Main Top-Level Database in MongoDB Compass
 ├── 📄 _system                     (Single consolidated collection for all platform metadata, history & RAG chunks)
 ├── 📄 demo_database               (Single consolidated collection containing the 5 demo table folders)
 │    ├── 🗂️ _id: "customers"       (table_name: "customers", document_count: 50, records: [50 docs])
 │    ├── 🗂️ _id: "employees"       (table_name: "employees", document_count: 60, records: [60 docs])
 │    ├── 🗂️ _id: "orders"          (table_name: "orders",    document_count: 120, records: [120 docs])
 │    ├── 🗂️ _id: "products"        (table_name: "products",  document_count: 12, records: [12 docs])
 │    └── 🗂️ _id: "students"        (table_name: "students",  document_count: 100, records: [100 docs])
 └── 📄 <uploaded_filename>         (1 single collection per uploaded dataset, e.g. brands, sales_2026)
```

## 2. Consolidated System Store (`knowurdb._system`)

All internal metadata is virtualized through `_SysCollectionProxy` (`backend/app/core/mongodb.py`) into the single `knowurdb._system` collection using `_sys_type` discriminators:

| Logical Store (`_sys_type`) | Purpose | Indexed Keys |
| :--- | :--- | :--- |
| `_sys_workspaces` | Workspace configuration and active dataset tracking | `(_sys_type, workspace_id)` |
| `_sys_sources` | Registry of all uploaded datasets, `database_name`, collections, and schema summaries | `(_sys_type, source_id)`, `(_sys_type, uploaded_at)` |
| `_sys_collections_metadata` | Per-collection document counts, index counts, `container_collection`, and parent `source_id` | `(_sys_type, source_id, collection_name)` |
| `_sys_query_history` | Audit log of executed natural language queries, MongoDB pipelines, timings, and row counts | `(_sys_type, id)`, `(_sys_type, created_at)` |
| `_sys_document_chunks` | Extracted text chunks and 128-dim L2-normalized vector embeddings for RAG | `(_sys_type, chunk_id)`, `(_sys_type, source_id, page_number)` |
| `_sys_settings` | Runtime AI provider and workspace preferences | `(_sys_type, key)` |

## 3. Consolidated Demo Container (`knowurdb.demo_database`)

`DemoGenerator` (`backend/app/services/demo_generator.py`) seeds all 5 demo tables inside a **single `demo_database` collection** inside `knowurdb`. Each document inside `demo_database` represents one table (`_id`: table name) with an expandable `records` array, and `MongoQueryExecutor` transparently unwraps it at query time via `[{"$match": {"_id": table}}, {"$unwind": "$records"}, {"$replaceRoot": {"newRoot": "$records"}}]`:
- **`products`** (`12` records): Product catalog with `category`, `price`, `stock`, `rating`, and embedded `tags[]` array.
- **`customers`** (`50` records): Customer profiles with nested `contact` (`{"email": ..., "phone": ...}`) and `address` (`{"city": ..., "state": ..., "country": "India"}`) sub-documents, plus `total_spent` and `loyalty_tier`.
- **`orders`** (`120` records): E-commerce orders with `customer_id`, `status`, `order_date`, `month`, `total_amount`, and an embedded `items[]` array.
- **`employees`** (`60` records): Organization directory with `department`, `role`, `salary`, and `performance_score`.
- **`students`** (`100` records): Academic records with `major`, `gpa`, `Attendance_Percentage`, and `credits_completed`.
