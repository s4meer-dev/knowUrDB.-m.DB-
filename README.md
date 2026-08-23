# knowUrDB

**Tagline:** Natural Language Database Intelligence Platform

**Current status**: Phase 5 — AI-powered Natural Language to SQL Integration

## Problem
Users often have databases but need SQL knowledge to extract information.

## Solution
knowUrDB allows users to interact with databases using natural language. It safely translates questions into SQL, runs queries securely, and returns the results. 

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
```

**Environment Variables:**
To enable AI-powered querying, create a `.env` file in the `backend/` directory:
```
# backend/.env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.6-flash
BACKEND_PORT=8000
FRONTEND_URL=http://localhost:5173
```
*Note: Never commit your actual API key to version control. The `.env` file is excluded via `.gitignore`.*

Run the server:
```bash
uvicorn app.main:app --reload
```

API runs at: `http://127.0.0.1:8000`
Swagger UI: `http://127.0.0.1:8000/docs`

**Key API Endpoints:**
- `GET /api/health` - Check backend health
- `GET /api/schema/summary` - View the active database schema
- `GET /api/ai/status` - Check AI integration status (requires `.env`)
- `POST /api/query` - Convert natural language to SQL and execute:
  ```json
  {"question": "How many students are in the database?"}
  ```

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

Testing and Linting (Oxlint):
```bash
cd frontend
npm run test
npm run lint
npm run build
```

## Architecture Overview
- **Frontend**: React, Vite, Tailwind CSS, Recharts
- **Backend**: FastAPI, Python, SQLAlchemy
- **Database**: SQLite
- **AI Integration**: Gemini API (gemini-3.6-flash)

### Project Phases
- **Phase 1:** Full-Stack Foundation (React, FastAPI, Axios) - **COMPLETE**
- **Phase 2:** Database Setup (SQLite demo with 4,000+ students and benchmark) - **COMPLETE**
- **Phase 3:** Natural Language to SQL Engine (Deterministic translation, API & Frontend) - **COMPLETE**
- **Phase 4:** Schema Intelligence & Introspection - **COMPLETE**
- **Phase 5:** AI LLM Integration (Gemini-powered semantic fallback) - **COMPLETE**

## Security Principles
- Never trust AI-generated SQL.
- Read-only queries enforce safety boundaries.
- No secrets in the frontend (API keys remain isolated on the backend).

## Testing Philosophy
- Isolated frontend and backend unit tests.
- AI benchmark evaluation suite to ensure robust SQL generation.
- Strict read-only database connections during runtime.

## GitHub Repository
[https://github.com/s4meer-dev/knowUrDB](https://github.com/s4meer-dev/knowUrDB)
