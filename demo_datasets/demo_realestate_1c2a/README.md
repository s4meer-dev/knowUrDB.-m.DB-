# Real Estate Portfolio (`demo_realestate_1c2a`)

> **Domain**: `realestate` | **Source Type**: `MongoDB` | **Total Documents**: `508` | **Collections**: `5`

Synthetic real estate dataset containing properties, agents, buyers, leases, and maintenance_requests.

## MongoDB Runtime & Filesystem Snapshot

- **MongoDB Database**: `demo_realestate_1c2a` (`mongodb://127.0.0.1:27017/demo_realestate_1c2a`)
- **Filesystem Snapshot Path**: `demo_datasets/demo_realestate_1c2a`
- **Content Hash**: `sha256:c2e3ce9ac2d467caead2bafd`
- **Generated At**: `2026-09-25T08:53:01.421738+00:00`

## Collections & JSONL Snapshots

| Collection | Documents | Snapshot File | Key Indexed Fields |
| :--- | ---: | :--- | :--- |
| `properties` | 118 | `collections/properties.jsonl` | `_id`, `propertie_id`, `name`, `tier`, `city`, `state` |
| `agents` | 73 | `collections/agents.jsonl` | `_id`, `agent_id`, `name`, `category`, `city`, `state` |
| `buyers` | 150 | `collections/buyers.jsonl` | `_id`, `buyer_id`, `propertie_id`, `entity_name`, `agent_id`, `category` |
| `leases` | 86 | `collections/leases.jsonl` | `_id`, `lease_id`, `propertie_id`, `name`, `category`, `score` |
| `maintenance_requests` | 81 | `collections/maintenance_requests.jsonl` | `_id`, `maintenance_request_id`, `agent_id`, `title`, `rating`, `amount` |

## Directory Structure

```text
demo_realestate_1c2a/
├── manifest.json
├── metadata.json
├── schema.json
├── README.md
└── collections/
    ├── properties.jsonl
    ├── agents.jsonl
    ├── buyers.jsonl
    ├── leases.jsonl
    └── maintenance_requests.jsonl
```
