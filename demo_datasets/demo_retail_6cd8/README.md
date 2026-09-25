# Omnichannel Retail Operations (`demo_retail_6cd8`)

> **Domain**: `retail` | **Source Type**: `MongoDB` | **Total Documents**: `550` | **Collections**: `5`

Synthetic retail store dataset containing stores, skus, pos_transactions, suppliers, and loyalty_members.

## MongoDB Runtime & Filesystem Snapshot

- **MongoDB Database**: `demo_retail_6cd8` (`mongodb://127.0.0.1:27017/demo_retail_6cd8`)
- **Filesystem Snapshot Path**: `demo_datasets/demo_retail_6cd8`
- **Content Hash**: `sha256:4e5b05b5ea9a55c3d880f191`
- **Generated At**: `2026-09-25T08:53:04.306959+00:00`

## Collections & JSONL Snapshots

| Collection | Documents | Snapshot File | Key Indexed Fields |
| :--- | ---: | :--- | :--- |
| `stores` | 106 | `collections/stores.jsonl` | `_id`, `store_id`, `name`, `tier`, `city`, `state` |
| `skus` | 69 | `collections/skus.jsonl` | `_id`, `sku_id`, `name`, `category`, `city`, `state` |
| `pos_transactions` | 147 | `collections/pos_transactions.jsonl` | `_id`, `pos_transaction_id`, `store_id`, `entity_name`, `sku_id`, `category` |
| `suppliers` | 110 | `collections/suppliers.jsonl` | `_id`, `supplier_id`, `store_id`, `name`, `category`, `score` |
| `loyalty_members` | 118 | `collections/loyalty_members.jsonl` | `_id`, `loyalty_member_id`, `sku_id`, `title`, `rating`, `amount` |

## Directory Structure

```text
demo_retail_6cd8/
├── manifest.json
├── metadata.json
├── schema.json
├── README.md
└── collections/
    ├── stores.jsonl
    ├── skus.jsonl
    ├── pos_transactions.jsonl
    ├── suppliers.jsonl
    └── loyalty_members.jsonl
```
