# knowUrDB

**Tagline:** Natural Language Database Intelligence Platform

**Current status**: Phase 1 — Full-Stack Development Foundation

## Problem
Users often have databases but need SQL knowledge to extract information.

## Solution
knowUrDB is planned to allow users to interact with databases using natural language. It is designed to safely translate questions into SQL, run queries securely, and explain the results.

## Development Setup

### Prerequisites
- Node.js (v20+)
- Python (v3.12+)

### Backend
Start the FastAPI server:
```bash
cd backend
python -m venv venv
.\venv\Scripts\Activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```
API runs at: `http://127.0.0.1:8000`
Health Endpoint: `GET /api/health`
Swagger UI: `http://127.0.0.1:8000/docs`

Testing and Linting:
```bash
cd backend
pytest -v
ruff check .
```

### Frontend
Start the React/Vite development server:
```bash
cd frontend
npm install
npm run dev
```
Frontend runs at: `http://localhost:5173`

Testing and Linting:
```bash
cd frontend
npm run test
npm run lint
npm run build
```

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
