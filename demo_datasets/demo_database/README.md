# Enterprise & Campus Intelligence (`demo_database`)

> **Domain**: `enterprise` | **Source Type**: `MongoDB` | **Total Documents**: `342` | **Collections**: `5`

Foundational multi-domain dataset containing customers, products, orders, employees, and students.

## MongoDB Runtime & Filesystem Snapshot

- **MongoDB Database**: `demo_database` (`mongodb://127.0.0.1:27017/demo_database`)
- **Filesystem Snapshot Path**: `demo_datasets/demo_database`
- **Content Hash**: `sha256:04356c5e2ebc9d370d88d7e6`
- **Generated At**: `2026-09-25T07:27:59.213519+00:00`

## Collections & JSONL Snapshots

| Collection | Documents | Snapshot File | Key Indexed Fields |
| :--- | ---: | :--- | :--- |
| `customers` | 50 | `collections/customers.jsonl` | `_id`, `customer_id`, `name`, `tier`, `total_spent`, `city` |
| `products` | 12 | `collections/products.jsonl` | `_id`, `product_id`, `name`, `category`, `price`, `stock` |
| `orders` | 120 | `collections/orders.jsonl` | `_id`, `order_id`, `customer_id`, `customer_name`, `status`, `month` |
| `employees` | 60 | `collections/employees.jsonl` | `_id`, `employee_id`, `name`, `department`, `role`, `salary` |
| `students` | 100 | `collections/students.jsonl` | `_id`, `student_id`, `first_name`, `last_name`, `name`, `department` |

## Directory Structure

```text
demo_database/
├── manifest.json
├── metadata.json
├── schema.json
├── README.md
└── collections/
    ├── customers.jsonl
    ├── products.jsonl
    ├── orders.jsonl
    ├── employees.jsonl
    └── students.jsonl
```
