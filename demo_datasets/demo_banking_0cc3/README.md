# Commercial Banking Hub (`demo_banking_0cc3`)

> **Domain**: `banking` | **Source Type**: `MongoDB` | **Total Documents**: `546` | **Collections**: `5`

Synthetic banking dataset containing clients, loan_accounts, credit_cards, wire_transfers, and risk_assessments.

## MongoDB Runtime & Filesystem Snapshot

- **MongoDB Database**: `demo_banking_0cc3` (`mongodb://127.0.0.1:27017/demo_banking_0cc3`)
- **Filesystem Snapshot Path**: `demo_datasets/demo_banking_0cc3`
- **Content Hash**: `sha256:d1d5f26dd271e23de5359766`
- **Generated At**: `2026-09-26T06:07:22.530045+00:00`

## Collections & JSONL Snapshots

| Collection | Documents | Snapshot File | Key Indexed Fields |
| :--- | ---: | :--- | :--- |
| `clients` | 106 | `collections/clients.jsonl` | `_id`, `client_id`, `name`, `tier`, `city`, `state` |
| `loan_accounts` | 65 | `collections/loan_accounts.jsonl` | `_id`, `loan_account_id`, `name`, `category`, `city`, `state` |
| `credit_cards` | 193 | `collections/credit_cards.jsonl` | `_id`, `credit_card_id`, `client_id`, `entity_name`, `loan_account_id`, `category` |
| `wire_transfers` | 99 | `collections/wire_transfers.jsonl` | `_id`, `wire_transfer_id`, `client_id`, `name`, `category`, `score` |
| `risk_assessments` | 83 | `collections/risk_assessments.jsonl` | `_id`, `risk_assessment_id`, `loan_account_id`, `title`, `rating`, `amount` |

## Directory Structure

```text
demo_banking_0cc3/
├── manifest.json
├── metadata.json
├── schema.json
├── README.md
└── collections/
    ├── clients.jsonl
    ├── loan_accounts.jsonl
    ├── credit_cards.jsonl
    ├── wire_transfers.jsonl
    └── risk_assessments.jsonl
```
