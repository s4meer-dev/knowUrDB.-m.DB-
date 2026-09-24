# Security Model & Read-Only Query Sandbox

## 1. `MongoQueryValidator` (`backend/app/services/mongo_validator.py`)

Every natural-language prompt and every generated MongoDB query specification is validated before execution:

1. **Allowed Operations**: Strictly restricted to `{"find", "aggregate", "count", "distinct"}`.
2. **Blocked Write & Admin Operations**: Rejects `insert`, `insertOne`, `insertMany`, `update`, `updateOne`, `updateMany`, `replaceOne`, `delete`, `deleteOne`, `deleteMany`, `remove`, `drop`, `dropDatabase`, `dropIndexes`, `createIndex`, `renameCollection`, `bulkWrite`, `findOneAndDelete`, `findOneAndUpdate`, and `findOneAndReplace`.
3. **Blocked Pipeline Stages & Server-Side JS**: Recursively scans all nested dicts and lists to block `$out`, `$merge`, `$where`, `$function`, `$accumulator`, `$currentOp`, `$collStats`, `eval`, and `mapReduce`.
4. **System Collection Isolation**: Blocks any query or `$lookup` stage targeting `_sys_*`, `system.*`, `admin`, `local`, or `config`.
5. **Execution Guardrails**: `MongoQueryExecutor` enforces `maxTimeMS` cursor timeouts and automatic `$limit` caps (`MAX_RESULT_LIMIT = 500`).
