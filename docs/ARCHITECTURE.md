# Architecture

## Conceptual Architecture

```
User
  ↓
React Frontend
  ↓
FastAPI Backend
  ↓
Application Services
  ├── Database Service
  ├── Schema Service
  ├── AI Service
  ├── SQL Validation Service
  ├── Query Execution Service
  └── Result/Visualization Service
```

## AI Service
```
AI Provider abstraction
  ↓
Gemini Provider
  ↓
Gemini API
```
The architecture must explicitly prevent the frontend from directly accessing Gemini. The Gemini API key must remain server-side.

## Database Service
```
Database Provider abstraction
  ↓
SQLite Provider
```

## AI Provider Architecture
The future backend will be designed around an AI provider abstraction:
- Avoid vendor lock-in.
- Support model configurability.
- Provide structured output.
- Enable prompt versioning.
- Handle retries, timeouts, and API errors.
- Ensure rate limit, token/cost awareness, and observability.
The application must not scatter Gemini-specific code throughout the backend.

## Database Provider Architecture
The database provider abstraction will handle:
- Connection lifecycle
- Schema introspection
- Read-only execution
- Query timeout strategy
- Row limits and result size limits
- Database isolation
- Uploaded database handling
