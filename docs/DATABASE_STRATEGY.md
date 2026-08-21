# Database Strategy

## Initial Database
SQLite.

## Demo Database (Phase 2 Completed)
A completely deterministic, realistic, SQLite-based benchmark database has been implemented for evaluating the knowUrDB Text-to-SQL engine.
See `DATABASE_DEMO.md` for full schema details, scaling information, and the benchmark dataset configuration.

**Key Distinction:** 
The demo database is *trusted, project-controlled data*. Future user-uploaded databases must still be treated as *untrusted input* subject to the constraints outlined below.

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
