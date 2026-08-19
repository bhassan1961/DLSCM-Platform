# DLSCM Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Client (Browser)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ Vue 3    │  │ Pinia    │  │ vue-i18n │  │ Leaflet │ │
│  │ Router   │  │ Stores   │  │ 6 langs  │  │ Maps    │ │
│  └────┬─────┘  └────┬─────┘  └──────────┘  └─────────┘ │
│       │              │                                   │
│  ┌────┴──────────────┴──────┐  ┌────────────────────┐   │
│  │   Axios HTTP Client      │  │  IndexedDB (CRDT)  │   │
│  │   JWT auto-refresh       │  │  Offline sync queue │   │
│  └────────────┬─────────────┘  └────────────────────┘   │
└───────────────┼─────────────────────────────────────────┘
                │ HTTP / WebSocket
┌───────────────┼─────────────────────────────────────────┐
│               │         FastAPI Server                   │
│  ┌────────────┴─────────────┐                           │
│  │   Middleware Stack        │                           │
│  │  ├─ SecurityHeaders      │                           │
│  │  ├─ RequestLogging        │                           │
│  │  ├─ RateLimit             │                           │
│  │  └─ CORS                  │                           │
│  └────────────┬─────────────┘                           │
│               │                                          │
│  ┌────────────┴─────────────┐  ┌────────────────────┐   │
│  │    26 API Routers         │  │  WebSocket Manager │   │
│  │    72 endpoints           │  │  Real-time events  │   │
│  └────────────┬─────────────┘  └────────────────────┘   │
│               │                                          │
│  ┌────────────┴─────────────┐  ┌────────────────────┐   │
│  │   12 Service Modules      │  │  Structured Logger │   │
│  │  ├─ Forecasting (ML)      │  │  JSON + corr. IDs  │   │
│  │  ├─ Risk Model (ML)       │  └────────────────────┘   │
│  │  ├─ Routing (OSRM)        │                           │
│  │  ├─ Prepositioning        │                           │
│  │  ├─ EDXL/CAP              │                           │
│  │  └─ Report Agent          │                           │
│  └────────────┬─────────────┘                           │
│               │                                          │
│  ┌────────────┴─────────────┐                           │
│  │   SQLAlchemy ORM          │                           │
│  │   17 Models + Alembic     │                           │
│  └────────────┬─────────────┘                           │
│               │                                          │
│  ┌────────────┴─────────────┐                           │
│  │   SQLite Database         │                           │
│  │   dlscm.db                │                           │
│  └──────────────────────────┘                           │
└─────────────────────────────────────────────────────────┘
```

## Frontend Architecture

### Component Hierarchy

```
App.vue
├── AppShell.vue (authenticated layout)
│   ├── Sidebar.vue (navigation, 25 routes)
│   ├── TopBar.vue (user info, language switcher, logout)
│   └── <router-view> (25 views)
│       ├── DashboardView.vue
│       ├── InventoryView.vue
│       ├── SupplyRequestsView.vue
│       ├── ShipmentsView.vue
│       ├── SuppliersView.vue
│       ├── KitAssemblyView.vue
│       ├── DonationsView.vue
│       ├── CrossOrgView.vue
│       ├── PrepositioningView.vue
│       ├── CrisisIntelView.vue
│       ├── CoordinationView.vue (3W)
│       ├── ForecastingView.vue
│       ├── RoutingView.vue
│       ├── ReportsView.vue
│       ├── ComplianceView.vue
│       ├── EdxlCapView.vue
│       ├── MarketplaceView.vue
│       ├── AfterActionView.vue
│       ├── RecoveryView.vue
│       ├── SimulationView.vue
│       ├── ResilienceView.vue (Risk Dashboard)
│       ├── CommunityView.vue
│       ├── AuditView.vue
│       └── SettingsView.vue
└── LoginView.vue (unauthenticated)
```

### Shared Components

| Component | Purpose |
|-----------|---------|
| `DataTable.vue` | Sortable, filterable tables with pagination |
| `MapView.vue` | Leaflet map with marker clustering |
| `StatCard.vue` | Dashboard metric cards with trend indicators |
| `StatusBadge.vue` | Color-coded status pills |
| `ErrorBanner.vue` | Dismissible error notifications with retry |

### State Management

```
Pinia Stores
├── auth.js      → JWT tokens, current user, login/logout
└── (component-local state for most views)
```

### i18n Architecture

```
src/i18n/
├── index.js           → vue-i18n configuration
└── locales/
    ├── en.json        → 784 keys (English)
    ├── ar.json        → 784 keys (Arabic, RTL)
    ├── fr.json        → 784 keys (French)
    ├── es.json        → 784 keys (Spanish)
    ├── zh.json        → 784 keys (Chinese)
    └── ru.json        → 784 keys (Russian)
```

RTL support via `[dir="rtl"]` CSS selectors applied when locale is `ar`.

### Offline Architecture

```
IndexedDB (dlscm-offline)
├── supply_requests    → Local queue for offline-created requests
├── sync_queue         → Pending operations awaiting connectivity
└── metadata           → Hybrid Logical Clock, Version Vector
```

CRDT conflict resolution:
- **HLC (Hybrid Logical Clock)** — Wall-clock + counter for causal ordering
- **LWW (Last-Writer-Wins)** — Per-field conflict resolution
- **VersionVector** — Detect concurrent modifications across devices

## Backend Architecture

### Middleware Pipeline

Requests flow through middleware in this order:

1. **CORS** — Origin validation
2. **SecurityHeadersMiddleware** — CSP, HSTS, X-Frame-Options, X-Content-Type-Options
3. **RequestLoggingMiddleware** — Structured JSON logging with correlation IDs (ContextVar)
4. **RateLimitMiddleware** — Per-IP request throttling

### Router Organization

| Router | Prefix | Endpoints |
|--------|--------|-----------|
| auth | `/api/v1/auth` | Login, user listing |
| dashboard | `/api/v1/dashboard` | Stats aggregation |
| inventory | `/api/v1/inventory` | Warehouses, stock, items |
| supply_requests | `/api/v1/supply-requests` | CRUD + status workflow |
| shipments | `/api/v1/shipments` | CRUD + tracking legs |
| disasters | `/api/v1/disasters` | Disaster events |
| alerts | `/api/v1/alerts` | Alert feed + acknowledge |
| intelligence | `/api/v1/intelligence` | Live RSS aggregation |
| coordination | `/api/v1/coordination` | 3W matrix |
| forecasting | `/api/v1/forecasting` | ML demand prediction |
| routing | `/api/v1/routing` | Route optimization |
| reports | `/api/v1/reports` | Donor report generation |
| marketplace | `/api/v1/marketplace` | Surge capacity matching |
| simulation | `/api/v1/simulation` | Scenario engine |
| risk | `/api/v1/risk` | Risk map + trends |
| edxl | `/api/v1/edxl` | CAP XML generation/parsing |
| suppliers | `/api/v1/suppliers` | Supplier registry |
| donations | `/api/v1/donations` | In-kind donations |
| kit_assembly | `/api/v1/kit-assembly` | Kit composition |
| cross_org | `/api/v1/cross-org` | Federated visibility |
| prepositioning | `/api/v1/prepositioning` | Stock optimization |
| compliance | `/api/v1/compliance` | Regulatory tracking |
| after_action | `/api/v1/after-action` | Post-response review |
| recovery | `/api/v1/recovery` | Recovery planning |
| community | `/api/v1/community` | Preparedness toolkit |
| audit | `/api/v1/audit` | Activity trail |

### Data Model

17 SQLAlchemy models:

```
Organization ──┐
               ├── User (role-based)
               ├── Warehouse ──── InventoryItem ──── StockLevel
               │
Disaster ──────├── SupplyRequest ──── RequestItem
               ├── Shipment ──── ShipmentLeg
               ├── Alert
               ├── CoordinationEntry (3W)
               └── AuditEntry

Supplier ──── SupplierItem
Donation
MarketplaceListing ──── Booking
```

### ML/AI Services

All models use scikit-learn and generate synthetic training data at prediction time for demo purposes.

| Service | File | Models Used |
|---------|------|-------------|
| Demand Forecasting | `services/forecasting.py` | GradientBoostingRegressor + STL decomposition |
| Risk Assessment | `services/risk_model.py` | RandomForestClassifier (trend), IsolationForest (anomaly) |
| Route Optimization | `services/routing.py` | OSRM client + haversine fallback |
| Prepositioning | `services/prepositioning.py` | Monte Carlo simulation + CVaR optimization |
| Report Generation | `services/report_agent.py` | Template-based with computed metrics |

### Database Migrations

Alembic manages schema changes:

```
backend/
├── alembic.ini
└── alembic/
    ├── env.py
    └── versions/
```

## Security Model

### Authentication Flow

```
Login → POST /api/v1/auth/login
      → Server validates credentials
      → Returns { access_token, refresh_token }
      → Client stores in localStorage (dlscm_access_token)
      → Axios interceptor attaches Bearer token
      → On 401 → refresh flow → retry original request
```

### Security Headers

```
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' ...
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
```

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for deployment instructions.
