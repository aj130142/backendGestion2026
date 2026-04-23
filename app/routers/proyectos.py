from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.models import Proyecto, ProyectoUsuario, HistorialEstado, Usuario, Cliente
from app.schemas.schemas import ProyectoCreate, ProyectoUpdate, ProyectoOut, AsignarUsuariosRequest
from app.auth.auth import check_permission, get_current_user

router = APIRouter(prefix="/proyectos", tags=["Proyectos"])


@router.get("/", response_model=list[ProyectoOut])
async def list_proyectos(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(check_permission("proyectos", "puede_ver")),
):
    result = await db.execute(
        select(Proyecto).options(
            selectinload(Proyecto.estado),
            selectinload(Proyecto.cliente).selectinload(Cliente.estado),
        )
    )
    return result.scalars().all()


@router.get("/{id_proyecto}", response_model=ProyectoOut)
async def get_proyecto(
    id_proyecto: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(check_permission("proyectos", "puede_ver")),
):
    result = await db.execute(
        select(Proyecto)
        .options(selectinload(Proyecto.estado), selectinload(Proyecto.cliente).selectinload(Cliente.estado))
        .where(Proyecto.id_proyecto == id_proyecto)
    )
    proyecto = result.scalar_one_or_none()
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return proyecto


@router.post("/", response_model=ProyectoOut, status_code=status.HTTP_201_CREATED)
async def create_proyecto(
    data: ProyectoCreate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(check_permission("proyectos", "puede_crear")),
):
    proyecto = Proyecto(**data.model_dump())
    db.add(proyecto)
    await db.commit()
    await db.refresh(proyecto)
    
    # Reload with relationships for the response
    result = await db.execute(
        select(Proyecto)
        .options(
            selectinload(Proyecto.estado),
            selectinload(Proyecto.cliente).selectinload(Cliente.estado),
        )
        .where(Proyecto.id_proyecto == proyecto.id_proyecto)
    )
    return result.scalar_one()


@router.put("/{id_proyecto}", response_model=ProyectoOut)
async def update_proyecto(
    id_proyecto: int,
    data: ProyectoUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(check_permission("proyectos", "puede_editar")),
):
    result = await db.execute(select(Proyecto).where(Proyecto.id_proyecto == id_proyecto))
    proyecto = result.scalar_one_or_none()
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    old_estado = proyecto.id_estado
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(proyecto, field, value)

    if data.id_estado and data.id_estado != old_estado:
        historial = HistorialEstado(
            entidad="proyecto",
            id_entidad=id_proyecto,
            id_estado_ant=old_estado,
            id_estado_nuevo=data.id_estado,
            id_usuario=current_user.id_usuario,
        )
        db.add(historial)

    await db.commit()
    await db.refresh(proyecto)
    
    # Reload with relationships for the response
    result = await db.execute(
        select(Proyecto)
        .options(
            selectinload(Proyecto.estado),
            selectinload(Proyecto.cliente).selectinload(Cliente.estado),
        )
        .where(Proyecto.id_proyecto == id_proyecto)
    )
    return result.scalar_one()


@router.delete("/{id_proyecto}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_proyecto(
    id_proyecto: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(check_permission("proyectos", "puede_eliminar")),
):
    result = await db.execute(select(Proyecto).where(Proyecto.id_proyecto == id_proyecto))
    proyecto = result.scalar_one_or_none()
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    await db.delete(proyecto)
    await db.commit()


@router.post("/{id_proyecto}/usuarios", status_code=status.HTTP_201_CREATED)
async def assign_usuarios(
    id_proyecto: int,
    data: AsignarUsuariosRequest,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(check_permission("proyectos", "puede_editar")),
):
    """Replace the assigned users for a project."""
    # Remove existing assignments
    await db.execute(
        delete(ProyectoUsuario).where(ProyectoUsuario.id_proyecto == id_proyecto)
    )
    # Add new
    for uid in data.id_usuarios:
        db.add(ProyectoUsuario(id_proyecto=id_proyecto, id_usuario=uid))
    await db.commit()
    return {"detail": "Usuarios asignados correctamente"}


@router.get("/{id_proyecto}/usuarios", response_model=list[int])
async def get_proyecto_usuarios(
    id_proyecto: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(check_permission("proyectos", "puede_ver")),
):
    result = await db.execute(
        select(ProyectoUsuario.id_usuario).where(ProyectoUsuario.id_proyecto == id_proyecto)
    )
    return [row[0] for row in result.all()]
