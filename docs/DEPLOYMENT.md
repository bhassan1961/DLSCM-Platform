# DLSCM Deployment Guide

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm 9+

### Backend Setup

```bash
cd backend
python -m venv venv

# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate

pip install -r requirements.txt
```

### Run Backend

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 5100 --reload
```

The server auto-seeds demo data on first startup. API documentation is available at `http://localhost:5100/docs`.

### Frontend Setup

```bash
cd frontend
npm install
```

### Run Frontend

```bash
npm run dev -- --port 3100
```

Access the app at `http://localhost:3100`.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./dlscm.db` | Database connection string |
| `SECRET_KEY` | (auto-generated) | JWT signing key |
| `CORS_ORIGINS` | `http://localhost:3100` | Allowed CORS origins |
| `LOG_LEVEL` | `INFO` | Logging level |
| `RATE_LIMIT_PER_MINUTE` | `60` | API rate limit per IP |

## Production Deployment

### Backend (Docker)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY backend/alembic.ini .
COPY backend/alembic ./alembic

EXPOSE 5100

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5100"]
```

### Frontend (Build)

```bash
cd frontend
npm run build
```

The `dist/` directory contains static files ready for any web server (Nginx, Caddy, S3+CloudFront, etc.).

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name dlscm.example.com;

    # Frontend static files
    location / {
        root /var/www/dlscm/dist;
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:5100;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket proxy
    location /ws/ {
        proxy_pass http://127.0.0.1:5100;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Database Migration

```bash
cd backend

# Generate a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1
```

## Production Checklist

- [ ] Set a strong `SECRET_KEY` environment variable
- [ ] Configure `CORS_ORIGINS` to match your domain
- [ ] Set `LOG_LEVEL=WARNING` for production
- [ ] Run behind a reverse proxy (Nginx/Caddy) with TLS
- [ ] Consider PostgreSQL for production database
- [ ] Set up log aggregation for structured JSON logs
- [ ] Configure rate limiting appropriate for expected traffic
- [ ] Enable database backups

## CI/CD

GitHub Actions workflow is configured in `.github/workflows/ci.yml`:

- **Triggers:** Push to `main`, pull requests
- **Backend:** Lint (flake8), test (pytest), security audit
- **Frontend:** Lint (ESLint), build verification, unit tests

## Monitoring

The backend emits structured JSON logs with correlation IDs. Each request is tagged with a unique `correlation_id` for tracing across log entries.

Log format:
```json
{
  "timestamp": "2026-08-19T10:30:00.000Z",
  "level": "INFO",
  "correlation_id": "abc123-def456",
  "method": "GET",
  "path": "/api/v1/dashboard/stats",
  "status_code": 200,
  "duration_ms": 45
}
```
