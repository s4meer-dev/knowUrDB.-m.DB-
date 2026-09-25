# E-Commerce Marketplace (`demo_ecommerce_10c6`)

> **Domain**: `ecommerce` | **Source Type**: `MongoDB` | **Total Documents**: `487` | **Collections**: `5`

Synthetic e-commerce marketplace dataset containing shoppers, catalog_items, carts, orders, and reviews.

## MongoDB Runtime & Filesystem Snapshot

- **MongoDB Database**: `demo_ecommerce_10c6` (`mongodb://127.0.0.1:27017/demo_ecommerce_10c6`)
- **Filesystem Snapshot Path**: `demo_datasets/demo_ecommerce_10c6`
- **Content Hash**: `sha256:0d115110a5b15dbe9fcb1803`
- **Generated At**: `2026-09-25T07:32:14.260892+00:00`

## Collections & JSONL Snapshots

| Collection | Documents | Snapshot File | Key Indexed Fields |
| :--- | ---: | :--- | :--- |
| `shoppers` | 83 | `collections/shoppers.jsonl` | `_id`, `shopper_id`, `name`, `tier`, `city`, `state` |
| `catalog_items` | 57 | `collections/catalog_items.jsonl` | `_id`, `catalog_item_id`, `name`, `category`, `city`, `state` |
| `carts` | 166 | `collections/carts.jsonl` | `_id`, `cart_id`, `shopper_id`, `entity_name`, `catalog_item_id`, `category` |
| `orders` | 105 | `collections/orders.jsonl` | `_id`, `order_id`, `shopper_id`, `name`, `category`, `score` |
| `reviews` | 76 | `collections/reviews.jsonl` | `_id`, `review_id`, `catalog_item_id`, `title`, `rating`, `amount` |

## Directory Structure

```text
demo_ecommerce_10c6/
├── manifest.json
├── metadata.json
├── schema.json
├── README.md
└── collections/
    ├── shoppers.jsonl
    ├── catalog_items.jsonl
    ├── carts.jsonl
    ├── orders.jsonl
    └── reviews.jsonl
```
