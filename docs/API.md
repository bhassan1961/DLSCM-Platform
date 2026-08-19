# DLSCM API Reference

Base URL: `http://localhost:5100/api/v1`

All endpoints require JWT authentication unless noted. Include the token as:
```
Authorization: Bearer <access_token>
```

## Authentication

### POST `/auth/login`
Login with user credentials. **No auth required.**

**Request:**
```json
{
  "username": "amina.osei",
  "password": "password"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "user": {
    "id": 1,
    "name": "Amina Osei",
    "email": "amina@ifrc.org",
    "role": "operations_director",
    "organization": "IFRC"
  }
}
```

### GET `/auth/users`
List all users (for demo login page).

---

## Dashboard

### GET `/dashboard/stats`
Aggregated dashboard statistics.

**Response:**
```json
{
  "active_disasters": 4,
  "pending_requests": 12,
  "in_transit_shipments": 8,
  "active_alerts": 6,
  "recent_disasters": [...],
  "recent_requests": [...],
  "recent_shipments": [...],
  "recent_alerts": [...]
}
```

---

## Inventory

### GET `/inventory/warehouses`
List all warehouses with stock summaries.

### GET `/inventory/items`
List catalog items with category filter.

**Query params:** `category` (optional)

### POST `/inventory/items`
Create a new catalog item.

### GET `/inventory/stock`
List stock levels across warehouses.

**Query params:** `warehouse_id`, `category` (optional)

### POST `/inventory/stock`
Add stock to a warehouse.

### PATCH `/inventory/stock/{id}`
Update stock quantity (inline editing).

---

## Supply Requests

### GET `/supply-requests`
List supply requests with pagination.

**Query params:** `status`, `disaster_id`, `page`, `per_page`

### POST `/supply-requests`
Create a new supply request.

**Request:**
```json
{
  "disaster_id": 1,
  "priority": "high",
  "items": [
    { "item_id": 1, "quantity": 500 }
  ],
  "notes": "Urgent medical supplies needed"
}
```

### PATCH `/supply-requests/{id}/status`
Update request status.

**Request:**
```json
{
  "status": "approved"
}
```

Valid status transitions: `pending` → `approved` → `sourcing` → `dispatched` → `delivered`

---

## Shipments

### GET `/shipments`
List shipments with optional filters.

**Query params:** `status`, `transport_mode`, `page`, `per_page`

### POST `/shipments`
Create a new shipment.

### GET `/shipments/{id}/tracking`
Get tracking details with individual legs.

**Response:**
```json
{
  "shipment_id": 1,
  "status": "in_transit",
  "transport_mode": "air",
  "legs": [
    {
      "origin": "Nairobi Hub",
      "destination": "Mogadishu Port",
      "status": "completed",
      "departed_at": "2026-08-15T08:00:00Z",
      "arrived_at": "2026-08-15T12:00:00Z"
    }
  ]
}
```

---

## Disasters

### GET `/disasters`
List active disasters.

### POST `/disasters`
Create a new disaster event.

---

## Alerts

### GET `/alerts`
List system alerts.

**Query params:** `severity`, `acknowledged`

### POST `/alerts/{id}/acknowledge`
Acknowledge an alert.

---

## Intelligence

### GET `/intelligence/live-alerts`
Aggregated live alerts from GDACS, ReliefWeb, ICRC.

### GET `/intelligence/news`
RSS feed aggregation from humanitarian news sources.

---

## Coordination (3W)

### GET `/coordination`
Who does What, Where matrix entries.

### POST `/coordination`
Add a 3W coordination entry.

---

## Forecasting

### GET `/forecasting/{disaster_id}`
ML-powered 14-day demand forecast.

**Response:**
```json
{
  "disaster_id": 1,
  "forecast_days": 14,
  "predictions": [
    {
      "date": "2026-08-20",
      "predicted_demand": 1250,
      "confidence_lower": 1100,
      "confidence_upper": 1400,
      "category": "medical"
    }
  ],
  "model": "GradientBoostingRegressor",
  "features_used": ["day_of_week", "severity", "population", "season"]
}
```

---

## Route Optimization

### POST `/routing/optimize`
Calculate optimal route between points.

**Request:**
```json
{
  "origin": { "lat": -1.2921, "lng": 36.8219 },
  "destination": { "lat": 2.0469, "lng": 45.3182 },
  "transport_mode": "road",
  "waypoints": []
}
```

**Response:**
```json
{
  "distance_km": 1847,
  "duration_hours": 28.5,
  "route_geometry": [...],
  "transport_mode": "road",
  "method": "osrm"
}
```

---

## Reports

### POST `/reports/generate`
Generate a donor report.

**Request:**
```json
{
  "template": "echo",
  "disaster_id": 1,
  "period_start": "2026-07-01",
  "period_end": "2026-08-01"
}
```

Templates: `echo` (EU ECHO), `usaid`, `fcdo`

---

## Marketplace

### GET `/marketplace`
List surge capacity listings.

### POST `/marketplace`
Create a new listing.

### POST `/marketplace/{id}/book`
Book a marketplace listing.

---

## Simulation

### POST `/simulation/run`
Run a disaster simulation scenario.

**Request:**
```json
{
  "disaster_type": "earthquake",
  "severity": 7.5,
  "location": { "lat": -1.29, "lng": 36.82 },
  "population_affected": 50000
}
```

---

## Risk Assessment

### GET `/risk/map`
Risk assessment across 8 global regions.

### GET `/risk/trends`
ML-predicted risk trends by region and hazard type.

---

## EDXL/CAP

### POST `/edxl/generate-cap`
Generate a CAP XML alert message.

### POST `/edxl/parse`
Parse an EDXL-DE or CAP XML message.

---

## Suppliers

### GET `/suppliers`
List registered suppliers.

### POST `/suppliers`
Register a new supplier.

---

## Additional Endpoints

| Group | Method | Path | Description |
|-------|--------|------|-------------|
| Donations | GET/POST | `/donations` | In-kind donation management |
| Kit Assembly | GET/POST | `/kit-assembly` | Aid kit composition |
| Cross-Org | GET | `/cross-org` | Federated stock visibility |
| Prepositioning | GET/POST | `/prepositioning` | Stock optimization |
| Compliance | GET | `/compliance` | Regulatory tracking |
| After-Action | GET/POST | `/after-action` | Post-response reviews |
| Recovery | GET/POST | `/recovery` | Recovery planning |
| Community | GET | `/community` | Preparedness toolkit |
| Audit | GET | `/audit` | Activity trail |

---

## Pagination

List endpoints support cursor and offset pagination:

**Query params:**
- `page` — Page number (offset pagination)
- `per_page` — Items per page (default: 20, max: 100)
- `cursor` — Cursor for cursor-based pagination

**Response headers:**
```
X-Total-Count: 150
X-Page: 1
X-Per-Page: 20
```

## Error Responses

```json
{
  "detail": "Human-readable error message"
}
```

| Status | Meaning |
|--------|---------|
| 400 | Bad request / validation error |
| 401 | Missing or expired JWT token |
| 403 | Insufficient permissions |
| 404 | Resource not found |
| 429 | Rate limit exceeded |
| 500 | Internal server error |

## Interactive Documentation

When the backend is running, visit `http://localhost:5100/docs` for the auto-generated Swagger UI with try-it-out capability.
