# knowUrDB

**Tagline:** Natural Language Database Intelligence Platform

**Status:** Phase 0 — Architecture Foundation

## Problem
Users often have databases but need SQL knowledge to extract information.

## Solution
knowUrDB allows users to interact with databases using natural language. It safely translates questions into SQL, runs queries securely, and explains the results.

## Architecture Overview
- **Frontend**: React, Vite, Tailwind CSS, Recharts
- **Backend**: FastAPI, Python, SQLAlchemy, SQLGlot
- **Database**: SQLite (initially)
- **AI**: Gemini API (with abstract provider architecture)

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
