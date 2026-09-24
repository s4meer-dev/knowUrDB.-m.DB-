# Natural Language to MongoDB Query Engine

## 1. Pipeline Generation (`MongoQueryService`)

Located in `backend/app/services/text_to_sql_service.py`, `MongoQueryService` translates natural-language questions into structured MongoDB query specifications:

```json
{
  "operation": "aggregate",
  "collection": "orders",
  "pipeline": [
    { "$match": { "status": "Completed" } },
    { "$unwind": "$items" },
    {
      "$group": {
        "_id": "$items.product_name",
        "total_revenue": { "$sum": "$items.line_total" },
        "units_sold": { "$sum": "$items.quantity" }
      }
    },
    { "$sort": { "total_revenue": -1 } },
    { "$limit": 10 },
    {
      "$project": {
        "_id": 0,
        "product_name": "$_id",
        "total_revenue": { "$round": ["$total_revenue", 2] },
        "units_sold": 1
      }
    }
  ],
  "display_query": "db.orders.aggregate([...])"
}
```

## 2. Hybrid AI + Deterministic Compilation

1. **Schema Introspection**: `MongoSchemaService` inspects BSON types, nested dot-paths (`contact.email`, `address.city`, `items[].price`), indexes, and sample documents.
2. **Gemini AI Generation**: Prompts Gemini with the exact MongoDB collection schema to emit a JSON query specification.
3. **Deterministic Aggregation Compiler**: When no external API key is configured or offline execution is requested, the deterministic compiler synthesizes `$match`, `$unwind`, `$group`, `$sort`, `$limit`, and `$count` stages directly from the question and live MongoDB schema.
