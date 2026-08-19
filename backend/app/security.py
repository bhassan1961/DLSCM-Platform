import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.logging_config import generate_request_id, get_logger, request_id_var

logger = get_logger("security")

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' ws: wss:",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("X-Request-ID") or generate_request_id()
        token = request_id_var.set(rid)
        start = time.perf_counter()
        try:
            response = await call_next(request)
            duration = (time.perf_counter() - start) * 1000
            response.headers["X-Request-ID"] = rid
            if request.url.path.startswith("/api/"):
                logger.info(
                    "%s %s %s %.0fms",
                    request.method,
                    request.url.path,
                    response.status_code,
                    duration,
                    extra={
                        "method": request.method,
                        "path": str(request.url.path),
                        "status_code": response.status_code,
                        "duration_ms": round(duration, 1),
                    },
                )
            return response
        except Exception:
            duration = (time.perf_counter() - start) * 1000
            logger.exception(
                "Unhandled error: %s %s",
                request.method,
                request.url.path,
                extra={
                    "method": request.method,
                    "path": str(request.url.path),
                    "duration_ms": round(duration, 1),
                },
            )
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )
        finally:
            request_id_var.reset(token)


_rate_buckets: dict[str, list[float]] = {}
RATE_LIMIT = 120
RATE_WINDOW = 60


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        bucket = _rate_buckets.setdefault(client_ip, [])
        bucket[:] = [t for t in bucket if now - t < RATE_WINDOW]

        if len(bucket) >= RATE_LIMIT:
            logger.warning("Rate limit exceeded for %s", client_ip)
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."},
                headers={"Retry-After": str(RATE_WINDOW)},
            )

        bucket.append(now)
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT)
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, RATE_LIMIT - len(bucket))
        )
        return response
