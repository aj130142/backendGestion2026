from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import Estado, Prioridad, Rol, Modulo, Usuario
from app.schemas.schemas import EstadoOut, PrioridadOut, RolOut, ModuloOut
from app.auth.auth import get_current_user

router = APIRouter(prefix="/catalogos", tags=["Catálogos"])


@router.get("/estados", response_model=list[EstadoOut])
async def list_estados(
    entidad: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    query = select(Estado)
    if entidad:
        query = query.where(Estado.entidad == entidad)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/prioridades", response_model=list[PrioridadOut])
async def list_prioridades(
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    result = await db.execute(select(Prioridad))
    return result.scalars().all()


@router.get("/roles", response_model=list[RolOut])
async def list_roles(
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    result = await db.execute(select(Rol))
    return result.scalars().all()


@router.get("/modulos", response_model=list[ModuloOut])
async def list_modulos(
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    result = await db.execute(select(Modulo))
    return result.scalars().all()
