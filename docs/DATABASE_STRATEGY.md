# Database Strategy

## Initial Database
SQLite.

## Demo Database
A realistic multi-table database will be created in a future phase. It should support:
- Joins
- Aggregations
- Filtering
- Sorting
- Date queries
- Foreign keys
- Analytical queries

## Future Schema Intelligence
Schema extraction should discover:
- Tables
- Columns
- Types
- Primary keys
- Foreign keys
- Indexes
- Relationships

Future large-database support may use schema retrieval instead of sending every table to the model.

## Untrusted Database Uploads
Uploaded databases will eventually be treated as untrusted input. Future database handling should consider and implement:
- file size limits
- file type validation
- SQLite integrity checks
- isolated storage
- read-only access
- cleanup of temporary files
- query execution limits
- result size limits
- database lifecycle management

*(Note: Do not implement these features now.)*
