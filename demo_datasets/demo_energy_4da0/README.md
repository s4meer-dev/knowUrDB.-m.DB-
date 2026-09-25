# Renewable Energy Grid (`demo_energy_4da0`)

> **Domain**: `energy` | **Source Type**: `MongoDB` | **Total Documents**: `515` | **Collections**: `5`

Synthetic energy grid dataset containing power_plants, smart_meters, grid_substations, energy_readings, and outage_events.

## MongoDB Runtime & Filesystem Snapshot

- **MongoDB Database**: `demo_energy_4da0` (`mongodb://127.0.0.1:27017/demo_energy_4da0`)
- **Filesystem Snapshot Path**: `demo_datasets/demo_energy_4da0`
- **Content Hash**: `sha256:82e471a55674bba40aa2efb7`
- **Generated At**: `2026-09-25T07:32:14.700432+00:00`

## Collections & JSONL Snapshots

| Collection | Documents | Snapshot File | Key Indexed Fields |
| :--- | ---: | :--- | :--- |
| `power_plants` | 75 | `collections/power_plants.jsonl` | `_id`, `power_plant_id`, `name`, `tier`, `city`, `state` |
| `smart_meters` | 41 | `collections/smart_meters.jsonl` | `_id`, `smart_meter_id`, `name`, `category`, `city`, `state` |
| `grid_substations` | 156 | `collections/grid_substations.jsonl` | `_id`, `grid_substation_id`, `power_plant_id`, `entity_name`, `smart_meter_id`, `category` |
| `energy_readings` | 124 | `collections/energy_readings.jsonl` | `_id`, `energy_reading_id`, `power_plant_id`, `name`, `category`, `score` |
| `outage_events` | 119 | `collections/outage_events.jsonl` | `_id`, `outage_event_id`, `smart_meter_id`, `title`, `rating`, `amount` |

## Directory Structure

```text
demo_energy_4da0/
├── manifest.json
├── metadata.json
├── schema.json
├── README.md
└── collections/
    ├── power_plants.jsonl
    ├── smart_meters.jsonl
    ├── grid_substations.jsonl
    ├── energy_readings.jsonl
    └── outage_events.jsonl
```
