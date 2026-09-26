# Hospitality & Resort Management (`demo_hospitality_be5f`)

> **Domain**: `hospitality` | **Source Type**: `MongoDB` | **Total Documents**: `535` | **Collections**: `5`

Synthetic hospitality dataset containing guests, hotels, rooms, reservations, and concierge_services.

## MongoDB Runtime & Filesystem Snapshot

- **MongoDB Database**: `demo_hospitality_be5f` (`mongodb://127.0.0.1:27017/demo_hospitality_be5f`)
- **Filesystem Snapshot Path**: `demo_datasets/demo_hospitality_be5f`
- **Content Hash**: `sha256:4d8536cbb77e37ff854f5ec5`
- **Generated At**: `2026-09-26T06:07:18.410936+00:00`

## Collections & JSONL Snapshots

| Collection | Documents | Snapshot File | Key Indexed Fields |
| :--- | ---: | :--- | :--- |
| `guests` | 84 | `collections/guests.jsonl` | `_id`, `guest_id`, `name`, `tier`, `city`, `state` |
| `hotels` | 67 | `collections/hotels.jsonl` | `_id`, `hotel_id`, `name`, `category`, `city`, `state` |
| `rooms` | 167 | `collections/rooms.jsonl` | `_id`, `room_id`, `guest_id`, `entity_name`, `hotel_id`, `category` |
| `reservations` | 104 | `collections/reservations.jsonl` | `_id`, `reservation_id`, `guest_id`, `name`, `category`, `score` |
| `concierge_services` | 113 | `collections/concierge_services.jsonl` | `_id`, `concierge_service_id`, `hotel_id`, `title`, `rating`, `amount` |

## Directory Structure

```text
demo_hospitality_be5f/
├── manifest.json
├── metadata.json
├── schema.json
├── README.md
└── collections/
    ├── guests.jsonl
    ├── hotels.jsonl
    ├── rooms.jsonl
    ├── reservations.jsonl
    └── concierge_services.jsonl
```
