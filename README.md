# DLSCM Platform

**Disaster Logistics & Supply Chain Management**

An end-to-end coordination platform for humanitarian supply chains — from warehouse to last mile, in every crisis.

## Overview

DLSCM unifies inventory management, supply chain coordination, AI-powered forecasting, and donor reporting into a single offline-first platform built for crisis environments. It supports all 6 UN languages (English, Arabic, French, Spanish, Chinese, Russian) with full RTL support.

### Key Capabilities

- **Real-time Operations Dashboard** — Live GDACS/ReliefWeb/ICRC news feeds, interactive Leaflet maps, disaster tracking, alert management
- **Multi-warehouse Inventory** — Stock CRUD with cross-org visibility, category filters, inline editing, expiry tracking
- **Supply Request Workflow** — Full lifecycle (pending → approved → sourcing → dispatched → delivered), offline-capable via IndexedDB
- **AI-Powered Forecasting** — GradientBoosting demand prediction with STL decomposition, 14-day projections, confidence intervals
- **Route Optimization** — Multi-modal (road/air/sea) routing via OSRM with haversine fallback
- **3W Coordination** — Who does What, Where — multi-agency matrix with live mapping
- **Donor Reporting** — ECHO, USAID, FCDO templates with automated metrics and expenditure breakdown
- **Surge Marketplace** — AI-matched resource sharing across organizations
- **Simulation Engine** — Disaster scenario builder with readiness scoring
- **Risk Dashboard** — RandomForest ML trend prediction across 8 global regions

## Architecture

```
dlscm/
├── backend/                    # Python FastAPI
│   ├── app/
│   │   ├── main.py             # App entry point with lifespan
│   │   ├── auth.py             # JWT authentication
│   │   ├── database.py         # SQLAlchemy + SQLite
│   │   ├── security.py         # Rate limiting, CSP, HSTS headers
│   │   ├── logging_config.py   # Structured JSON logging + correlation IDs
│   │   ├── websocket_manager.py# WebSocket connection manager
│   │   ├── pagination.py       # Cursor/offset pagination
│   │   ├── seed.py             # Demo data seeding
│   │   ├── models/             # 17 SQLAlchemy models
│   │   ├── routers/            # 26 API routers (72 endpoints)
│   │   └── services/           # 12 service modules (ML, routing, EDXL)
│   ├── alembic.ini             # Database migration config
│   └── requirements.txt
├── frontend/                   # Vue 3 + Vite
│   ├── src/
│   │   ├── views/              # 25 operational views
│   │   ├── components/         # 8 reusable UI components
│   │   ├── composables/        # useErrorHandler, useOffline
│   │   ├── i18n/locales/       # 6 locale files (784 keys each)
│   │   ├── stores/             # Pinia state management
│   │   └── api/client.js       # Axios with JWT refresh
│   └── index.html
└── package.json
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vue 3, Vite, Vue Router, Pinia, vue-i18n |
| Maps | Leaflet with OpenStreetMap |
| Charts | Chart.js |
| Backend | Python 3.11+, FastAPI, Uvicorn |
| Database | SQLite + SQLAlchemy ORM |
| Migrations | Alembic |
| ML/AI | scikit-learn (GradientBoosting, RandomForest, IsolationForest) |
| Routing | OSRM (Open Source Routing Machine) |
| Real-time | WebSockets |
| Offline | IndexedDB with CRDT sync (HLC + LWW + VersionVector) |
| Auth | JWT with refresh tokens |
| CI/CD | GitHub Actions |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 5100 --reload
```

The backend auto-seeds demo data on first run (5 organizations, 8 users, 6 warehouses, 20 items, 4 disasters, 8 alerts, and more).

### Frontend

```bash
cd frontend
npm install
npm run dev -- --port 3100
```

### Access

- **Frontend**: http://localhost:3100
- **API Docs**: http://localhost:5100/docs (Swagger UI)
- **Login**: Click any demo user on the login page (no credentials needed)

## Demo Users

| Name | Role | Organization |
|------|------|-------------|
| Amina Osei | Operations Director | IFRC |
| Lars Bergstrom | Field Coordinator | IFRC |
| Claire Dubois | Supply Manager | MSF Logistics |
| Paolo Rossi | Operations Director | WFP |
| Fatima Njeri | Compliance Officer | WFP |
| James Kamau | Field Coordinator | Kenya Red Cross |
| Sarah Wanjiku | Supply Manager | Kenya Red Cross |
| Hans Mueller | Operations Director | DHL Disaster Response |

## Platform Views (25)

### Phase 1 — Foundation
| View | Description |
|------|-------------|
| Dashboard | Real-time stats, Leaflet map, GDACS/ReliefWeb/ICRC live news ticker, alert feed, Live TV modal |
| Inventory | Multi-warehouse stock tracking with inline quantity editing, category filters |
| Supply Requests | Full lifecycle workflow with offline IndexedDB support |
| Shipments | Multi-modal tracking (road/air/sea), customs status, leg-level detail |
| Suppliers | Registry with pre-qualification, ML disruption prediction |
| Kit Assembly | Create aid kits from item catalog components |
| Donations | In-kind donation intake with quality assessment |
| Cross-Org Visibility | Federated stock visibility across organizations |
| Prepositioning | Monte Carlo stochastic optimization for pre-disaster stock placement |

### Phase 2 — Intelligence
| View | Description |
|------|-------------|
| Crisis Intelligence | ReliefWeb, GDACS, ICRC feed aggregation |
| 3W Coordination | Who/What/Where matrix with map visualization |
| Demand Forecasting | 14-day ML projections with confidence intervals |
| Route Optimization | Multi-modal route planning via OSRM |
| Donor Reports | ECHO, USAID, FCDO automated reporting |
| Compliance | Regulatory tracking dashboard |
| EDXL/CAP Exchange | Generate and parse EDXL-DE/CAP XML messages |

### Phase 3 — Scale
| View | Description |
|------|-------------|
| Surge Marketplace | Capacity sharing with AI matching and booking |
| After-Action Review | Post-response analysis with scoring |
| Recovery Planning | 5-phase recovery lifecycle with procurement tracking |

### Phase 4 — Ecosystem
| View | Description |
|------|-------------|
| Simulation | Scenario builder with disaster type/severity parameters |
| Risk Dashboard | 8-region risk assessment with RandomForest trend prediction |
| Community Toolkit | Disaster preparedness checklist with progress tracking |
| Audit Trail | System activity log with filtering |
| Settings | Language, theme, profile preferences |

## Internationalization

Full i18n with 784 translation keys across 6 UN languages:

| Language | Code | Direction | Status |
|----------|------|-----------|--------|
| English | en | LTR | Complete |
| Arabic | ar | RTL | Complete — native translations |
| French | fr | LTR | Complete — native translations |
| Spanish | es | LTR | Complete — native translations |
| Chinese | zh | LTR | Complete — native translations |
| Russian | ru | LTR | Complete — native translations |

## AI/ML Models

All ML models use scikit-learn and run locally — no external API keys required.

| Model | Algorithm | Purpose |
|-------|-----------|---------|
| Demand Forecasting | GradientBoostingRegressor | 14-day supply demand projection with STL decomposition |
| Risk Prediction | RandomForestClassifier | Trend prediction across 4 hazard types, 8 regions |
| Supply Disruption | IsolationForest + GBClassifier | Supplier performance anomaly detection |
| Anomaly Detection | IsolationForest + EWMA | Inventory/shipment anomalies and consumption drift |
| Prepositioning | Monte Carlo + CVaR | Stochastic optimization across 200 scenarios |
| Sitrep Parsing | Keyword NLP | Extract disaster type, urgency, needs from situation reports |

## API Reference

72 endpoints across 26 routers under `/api/v1/`:

| Group | Key Endpoints |
|-------|--------------|
| Auth | `POST /auth/login`, `GET /auth/users` |
| Dashboard | `GET /dashboard/stats` |
| Inventory | `GET /inventory/warehouses`, `GET,POST /inventory/stock`, `GET,POST /inventory/items` |
| Supply Requests | `GET,POST /supply-requests`, `PATCH /supply-requests/:id/status` |
| Shipments | `GET,POST /shipments`, `GET /shipments/:id/tracking` |
| Disasters | `GET,POST /disasters` |
| Alerts | `GET /alerts`, `POST /alerts/:id/acknowledge` |
| Intelligence | `GET /intelligence/live-alerts`, `GET /intelligence/news` |
| Coordination | `GET,POST /coordination` |
| Forecasting | `GET /forecasting/:disaster_id` |
| Routing | `POST /routing/optimize` |
| Reports | `POST /reports/generate` |
| Marketplace | `GET,POST /marketplace`, `POST /marketplace/:id/book` |
| Simulation | `POST /simulation/run` |
| Risk | `GET /risk/map`, `GET /risk/trends` |
| EDXL | `POST /edxl/generate-cap`, `POST /edxl/parse` |

Interactive docs available at `http://localhost:5100/docs` when the backend is running.

## Security

- JWT authentication with refresh tokens and auto-renewal
- Rate limiting on all API endpoints
- Security headers: CSP, HSTS, X-Frame-Options, X-Content-Type-Options
- CORS policy enforcement
- Structured JSON logging with request correlation IDs
- Global exception handler (no stack traces in production)

## Offline Support

- IndexedDB for local data persistence
- CRDT-based conflict resolution (Hybrid Logical Clock + Last-Writer-Wins + VersionVector)
- Background sync queue for automatic reconnection
- Currently enabled for Supply Requests workflow

## Standards Compliance

- **EDXL-DE / CAP** — Common Alerting Protocol message generation and parsing
- **OCHA 3W** — Who does What, Where coordination matrix
- **Sphere Standards** — Humanitarian response quality benchmarks referenced in compliance view

## License

MIT — Open source for humanitarian use.
