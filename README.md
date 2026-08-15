# DLSCM - Disaster Logistics & Supply Chain Management Platform

A full-stack platform for coordinating humanitarian supply chains across the disaster management lifecycle: preparedness, response, recovery, and mitigation.

## Tech Stack

- **Frontend**: Vue 3 + Vite + Vue Router + Pinia (port 3100)
- **Backend**: Python FastAPI + SQLAlchemy + SQLite (port 5100)
- **Maps**: Leaflet.js
- **Charts**: Chart.js via vue-chartjs
- **AI/ML**: Deterministic algorithms (no external API keys required)

## Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
python run.py
```

The backend starts on `http://localhost:5100` and auto-seeds the database on first run.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend starts on `http://localhost:3100` with a Vite proxy forwarding `/api` requests to the backend.

### Login

Use any email address at the login screen (e.g., `admin@dlscm.org`). Authentication is simplified for demo purposes.

## Platform Views

### Phase 1 - Foundation
- **Dashboard** - Real-time stats, alert feed, active shipments, and supply category breakdown chart
- **Inventory** - Multi-warehouse stock tracking with item-level detail
- **Supply Requests** - Request creation and fulfillment workflow with status tracking
- **Shipments** - Shipment tracking with status badges

### Phase 2 - Intelligence
- **3W Coordination** - Who/What/Where entries showing multi-org disaster response activities
- **Demand Forecast** - AI-powered demand projections by supply category with interactive charts
- **Route Optimizer** - Multi-leg route planning with Leaflet map visualization
- **Donor Reports** - Automated report generation with executive summary and key metrics
- **Sitrep Parser** - NLP-based situation report parsing extracting disaster type, urgency, needs, and affected population

### Phase 3 - Scale
- **Surge Marketplace** - Shared capacity listings for warehouse space, transport, and personnel

### Phase 4 - Ecosystem
- **Simulation** - Scenario builder modeling disaster response (cost, damage, readiness, demand)
- **Risk Dashboard** - Multi-hazard risk map with 8 global regions and composite scoring
- **Community Toolkit** - Disaster preparedness checklists with progress tracking
- **Settings** - User profile and platform preferences

## Project Structure

```
dlscm/
  backend/
    app/
      models/        # SQLAlchemy models (14 tables)
      routers/       # FastAPI route handlers
      services/      # Deterministic AI/ML services
      database.py    # SQLite connection + session
      main.py        # FastAPI app with CORS + router registration
      seed.py        # Demo data seeder
    run.py           # Uvicorn entrypoint
  frontend/
    src/
      api/           # Axios API client
      components/    # Reusable UI components (DataTable, MapView, StatCard, etc.)
      views/         # Page-level Vue components (13 views)
      stores/        # Pinia stores (auth, notifications)
      router.js      # Vue Router config
    vite.config.js   # Vite config with API proxy
```

## API Endpoints

All endpoints are under `/api/v1/`:

| Module | Endpoints |
|--------|-----------|
| Auth | `POST /auth/login`, `GET /auth/users` |
| Dashboard | `GET /dashboard/stats` |
| Inventory | `GET /inventory/warehouses`, `GET /inventory/stock` |
| Requests | `GET /requests`, `POST /requests`, `PATCH /requests/:id/status` |
| Disasters | `GET /disasters`, `GET /disasters/:id` |
| Alerts | `GET /alerts`, `POST /alerts/:id/acknowledge` |
| Shipments | `GET /shipments` |
| Coordination | `GET /coordination` |
| Forecasting | `GET /forecasting/:disaster_id` |
| Routing | `POST /routing/optimize` |
| Reports | `POST /reports/generate` |
| Sitrep | `POST /sitrep/parse` |
| Marketplace | `GET /marketplace` |
| Simulation | `POST /simulation/run`, `GET /simulation/scenarios` |
| Risk | `GET /risk/map` |
