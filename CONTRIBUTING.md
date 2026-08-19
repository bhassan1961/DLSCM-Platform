# Contributing to DLSCM

Thank you for your interest in contributing to the Disaster Logistics & Supply Chain Management Platform.

## Development Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm 9+

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

The backend starts on `http://localhost:5100` and auto-seeds the SQLite database on first run.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend starts on `http://localhost:3100` with API requests proxied to the backend.

### Docker (alternative)

```bash
docker compose up --build
```

This starts both services. The frontend is available at `http://localhost:3100`.

## Project Structure

- `backend/app/models/` — SQLAlchemy models (one file per domain)
- `backend/app/routers/` — FastAPI route handlers with Pydantic schemas
- `backend/app/services/` — Deterministic AI/ML services
- `backend/app/seed.py` — Demo data seeder
- `frontend/src/views/` — Page-level Vue components
- `frontend/src/components/` — Reusable UI components
- `frontend/src/api/client.js` — Axios API client

## Conventions

- **Backend**: Pydantic v2 with `ConfigDict(from_attributes=True)`. Router prefix pattern: `/api/v1/<resource>`.
- **Frontend**: Vue 3 Composition API (`<script setup>`). CSS custom properties for theming.
- **Commits**: Use conventional commit messages (`feat:`, `fix:`, `docs:`, `refactor:`).

## Adding a New Feature

1. Create the model in `backend/app/models/` and register it in `__init__.py`
2. Create the router in `backend/app/routers/` and register it in `main.py`
3. Add seed data in `backend/app/seed.py`
4. Add the API client export in `frontend/src/api/client.js`
5. Create the view in `frontend/src/views/`
6. Add the route in `frontend/src/router.js`
7. Add the sidebar link in `frontend/src/components/layout/Sidebar.vue`

## Reporting Issues

Open an issue with:
- Steps to reproduce
- Expected vs actual behavior
- Browser/OS information if frontend-related
