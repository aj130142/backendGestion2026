import logging

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.routers import auth, usuarios, clientes, proyectos, tareas, historial, catalogos, permisos
from app.database import get_db
from app.config import settings
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware


# ─── Logging ──────────────────────────────────────────────────────────────────
logger = logging.getLogger("techsolutions")
logging.basicConfig(level=logging.INFO)

# ─── Rate Limiter (#13 — slowapi) ─────────────────────────────────────────────
from app.limiter import limiter


# ─── Security Headers Middleware (#10 / #14 — CSP, HSTS, X-Frame-Options) ────

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Agrega cabeceras de seguridad HTTP a todas las respuestas.
    Protege contra: Clickjacking, MIME sniffing, XSS, referrer leaks, etc."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # Prevenir Clickjacking (#14)
        response.headers["X-Frame-Options"] = "DENY"
        # Refuerzo anti-clickjacking moderno
        response.headers["Content-Security-Policy"] = "frame-ancestors 'none'"
        # Prevenir MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        # Capa adicional anti-XSS (legacy pero aún útil)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        # Controlar información del referrer
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Restringir APIs del navegador que no se necesitan
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )
        # Forzar HTTPS (solo activar cuando se despliegue con HTTPS)
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response


# ─── App Setup ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="TechSolutions S.A. — API",
    description="Sistema de gestión de clientes, proyectos y tareas.",
    version="1.0.0",
    # En producción, desactivar la documentación interactiva
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
)

# ─── Rate Limiter: registrar en el estado de la app ───────────────────────────
app.state.limiter = limiter


# ─── Global Exception Handler (#4 — no exponer errores internos) ─────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Captura excepciones no manejadas y devuelve un mensaje genérico
    en producción, evitando exponer detalles internos del backend."""
    logger.error(f"Error no manejado en {request.method} {request.url}: {exc}", exc_info=True)

    if settings.ENVIRONMENT == "production":
        return JSONResponse(
            status_code=500,
            content={"detail": "Error interno del servidor. Contacta al administrador."},
        )
    else:
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc)},
        )


# ─── Rate Limit Exception Handler (#13) ──────────────────────────────────────
# Responde con 429 Too Many Requests cuando se supera el límite
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ─── Middleware: Rate Limiting (#13) ──────────────────────────────────────────
app.add_middleware(SlowAPIMiddleware)

# ─── Middleware: Security Headers (#10 / #14) ─────────────────────────────────
app.add_middleware(SecurityHeadersMiddleware)

# ─── Middleware: Proxy Headers (Soporte HTTPS en Railway) ─────────────────────
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# ─── Middleware: CORS seguro (#3 — restringir orígenes) ───────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


# ─── Routers ─────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(clientes.router)
app.include_router(proyectos.router)
app.include_router(tareas.router)
app.include_router(historial.router)
app.include_router(catalogos.router)
app.include_router(permisos.router)


# ─── Health Endpoints ────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "message": "TechSolutions API está corriendo ✓"}


@app.get("/health", tags=["Health"])
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "conectada ✓"}
    except Exception as e:
        logger.error(f"Health check falló: {e}", exc_info=True)
        return {"status": "error", "database": "no disponible"}
