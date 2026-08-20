# knowUrDB

**Tagline:** Natural Language Database Intelligence Platform

**Current status:** Phase 0 — Architecture Foundation

## Problem
Users often have databases but need SQL knowledge to extract information.

## Solution
knowUrDB is planned to allow users to interact with databases using natural language. It is designed to safely translate questions into SQL, run queries securely, and explain the results.

*(Note: Text-to-SQL functionality, database upload, and Gemini integration are planned features and do not yet exist.)*

## Architecture Overview
- **Frontend**: React, Vite, Tailwind CSS, Recharts (Planned)
- **Backend**: FastAPI, Python, SQLAlchemy, SQLGlot (Planned)
- **Database**: SQLite initially (Planned)
- **AI**: Gemini API with abstract provider architecture (Planned)

## Roadmap
Please see [DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md) for the detailed phase-by-phase roadmap.

## Security Principles
- Never trust AI-generated SQL.
- Read-only queries enforce safety boundaries.
- No secrets in the frontend.

## Testing Philosophy
- Isolated frontend and backend unit tests.
- AI benchmark evaluation suite to ensure robust SQL generation.

## Development
(Placeholder for development instructions to be added in Phase 1)

## GitHub Repository
[https://github.com/s4meer-dev/knowUrDB](https://github.com/s4meer-dev/knowUrDB)
