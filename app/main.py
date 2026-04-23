from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.routers import auth, usuarios, clientes, proyectos, tareas, historial, catalogos, permisos
from app.database import get_db

app = FastAPI(
    title="TechSolutions S.A. — API",
    description="Sistema de gestión de clientes, proyectos y tareas.",
    version="1.0.0",
)

# Allow Flutter web and local dev to reach the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Narrow this to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(clientes.router)
app.include_router(proyectos.router)
app.include_router(tareas.router)
app.include_router(historial.router)
app.include_router(catalogos.router)
app.include_router(permisos.router)


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "message": "TechSolutions API está corriendo ✓"}


@app.get("/health", tags=["Health"])
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "conectada ✓"}
    except Exception as e:
        return {"status": "error", "database": str(e)}
