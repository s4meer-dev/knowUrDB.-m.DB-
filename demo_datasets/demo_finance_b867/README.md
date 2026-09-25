# Financial Operations (`demo_finance_b867`)

> **Domain**: `finance` | **Source Type**: `MongoDB` | **Total Documents**: `681` | **Collections**: `5`

Synthetic financial operations dataset containing customers, accounts, transactions, investments, and branches.

## MongoDB Runtime & Filesystem Snapshot

- **MongoDB Database**: `demo_finance_b867` (`mongodb://127.0.0.1:27017/demo_finance_b867`)
- **Filesystem Snapshot Path**: `demo_datasets/demo_finance_b867`
- **Content Hash**: `sha256:4e197dbb9f53dd582ffe3c09`
- **Generated At**: `2026-09-25T07:32:16.143571+00:00`

## Collections & JSONL Snapshots

| Collection | Documents | Snapshot File | Key Indexed Fields |
| :--- | ---: | :--- | :--- |
| `customers` | 114 | `collections/customers.jsonl` | `_id`, `customer_id`, `name`, `segment`, `credit_score`, `city` |
| `accounts` | 177 | `collections/accounts.jsonl` | `_id`, `account_number`, `customer_id`, `customer_name`, `branch_id`, `account_type` |
| `transactions` | 271 | `collections/transactions.jsonl` | `_id`, `transaction_id`, `account_number`, `customer_id`, `branch_id`, `transaction_type` |
| `investments` | 101 | `collections/investments.jsonl` | `_id`, `investment_id`, `customer_id`, `customer_name`, `asset_class`, `principal` |
| `branches` | 18 | `collections/branches.jsonl` | `_id`, `branch_id`, `name`, `city`, `state`, `assets_under_management` |

## Directory Structure

```text
demo_finance_b867/
├── manifest.json
├── metadata.json
├── schema.json
├── README.md
└── collections/
    ├── customers.jsonl
    ├── accounts.jsonl
    ├── transactions.jsonl
    ├── investments.jsonl
    └── branches.jsonl
```
