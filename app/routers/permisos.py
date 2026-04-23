from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import RolPermiso, Modulo, Usuario
from app.schemas.schemas import RolPermisoBase, RolPermisoOut
from app.auth.auth import check_permission

router = APIRouter(prefix="/rol-permisos", tags=["Permisos por Rol"])


@router.get("/", response_model=list[RolPermisoOut])
async def list_permisos(
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(check_permission("usuarios", "puede_ver")),
):
    result = await db.execute(
        select(RolPermiso).options(selectinload(RolPermiso.modulo))
    )
    return result.scalars().all()


@router.get("/{id_rol}", response_model=list[RolPermisoOut])
async def get_permisos_rol(
    id_rol: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(check_permission("usuarios", "puede_ver")),
):
    result = await db.execute(
        select(RolPermiso)
        .options(selectinload(RolPermiso.modulo))
        .where(RolPermiso.id_rol == id_rol)
    )
    return result.scalars().all()


@router.put("/", response_model=RolPermisoOut)
async def upsert_permiso(
    data: RolPermisoBase,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(check_permission("usuarios", "puede_editar")),
):
    """Create or update a permission entry for a role+module combination."""
    result = await db.execute(
        select(RolPermiso).where(
            RolPermiso.id_rol == data.id_rol,
            RolPermiso.id_modulo == data.id_modulo,
        )
    )
    permiso = result.scalar_one_or_none()

    if permiso:
        permiso.puede_ver = data.puede_ver
        permiso.puede_crear = data.puede_crear
        permiso.puede_editar = data.puede_editar
        permiso.puede_eliminar = data.puede_eliminar
    else:
        permiso = RolPermiso(**data.model_dump())
        db.add(permiso)

    await db.commit()
    await db.refresh(permiso)
    
    # Reload with relationships for the response
    result = await db.execute(
        select(RolPermiso)
        .options(selectinload(RolPermiso.modulo))
        .where(
            RolPermiso.id_rol == permiso.id_rol,
            RolPermiso.id_modulo == permiso.id_modulo,
        )
    )
    return result.scalar_one()
