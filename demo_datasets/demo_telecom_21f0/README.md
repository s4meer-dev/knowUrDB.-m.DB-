# Telecommunications Network (`demo_telecom_21f0`)

> **Domain**: `telecom` | **Source Type**: `MongoDB` | **Total Documents**: `545` | **Collections**: `5`

Synthetic telecom network dataset containing subscribers, cell_towers, data_plans, call_records, and network_incidents.

## MongoDB Runtime & Filesystem Snapshot

- **MongoDB Database**: `demo_telecom_21f0` (`mongodb://127.0.0.1:27017/demo_telecom_21f0`)
- **Filesystem Snapshot Path**: `demo_datasets/demo_telecom_21f0`
- **Content Hash**: `sha256:e6357bef15c5f40162b74ccf`
- **Generated At**: `2026-09-25T07:32:15.160602+00:00`

## Collections & JSONL Snapshots

| Collection | Documents | Snapshot File | Key Indexed Fields |
| :--- | ---: | :--- | :--- |
| `subscribers` | 127 | `collections/subscribers.jsonl` | `_id`, `subscriber_id`, `name`, `tier`, `city`, `state` |
| `cell_towers` | 42 | `collections/cell_towers.jsonl` | `_id`, `cell_tower_id`, `name`, `category`, `city`, `state` |
| `data_plans` | 148 | `collections/data_plans.jsonl` | `_id`, `data_plan_id`, `subscriber_id`, `entity_name`, `cell_tower_id`, `category` |
| `call_records` | 125 | `collections/call_records.jsonl` | `_id`, `call_record_id`, `subscriber_id`, `name`, `category`, `score` |
| `network_incidents` | 103 | `collections/network_incidents.jsonl` | `_id`, `network_incident_id`, `cell_tower_id`, `title`, `rating`, `amount` |

## Directory Structure

```text
demo_telecom_21f0/
├── manifest.json
├── metadata.json
├── schema.json
├── README.md
└── collections/
    ├── subscribers.jsonl
    ├── cell_towers.jsonl
    ├── data_plans.jsonl
    ├── call_records.jsonl
    └── network_incidents.jsonl
```
