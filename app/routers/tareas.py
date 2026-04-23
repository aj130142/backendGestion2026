from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.models import Tarea, TareaUsuario, HistorialEstado, Usuario, Proyecto
from app.schemas.schemas import TareaCreate, TareaUpdate, TareaOut, AsignarUsuariosRequest
from app.auth.auth import check_permission

router = APIRouter(prefix="/tareas", tags=["Tareas"])


@router.get("/", response_model=list[TareaOut])
async def list_tareas(
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(check_permission("tareas", "puede_ver")),
):
    result = await db.execute(
        select(Tarea).options(
            selectinload(Tarea.estado),
            selectinload(Tarea.prioridad),
            selectinload(Tarea.usuarios).selectinload(TareaUsuario.usuario).selectinload(Usuario.rol),
        )
    )
    return result.scalars().all()


@router.get("/{id_tarea}", response_model=TareaOut)
async def get_tarea(
    id_tarea: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(check_permission("tareas", "puede_ver")),
):
    result = await db.execute(
        select(Tarea)
        .options(
            selectinload(Tarea.estado), 
            selectinload(Tarea.prioridad),
            selectinload(Tarea.usuarios).selectinload(TareaUsuario.usuario).selectinload(Usuario.rol)
        )
        .where(Tarea.id_tarea == id_tarea)
    )
    tarea = result.scalar_one_or_none()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return tarea


@router.post("/", response_model=TareaOut, status_code=status.HTTP_201_CREATED)
async def create_tarea(
    data: TareaCreate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(check_permission("tareas", "puede_crear")),
):
    # Validation: dates must be within project range
    result = await db.execute(select(Proyecto).where(Proyecto.id_proyecto == data.id_proyecto))
    proyecto = result.scalar_one_or_none()
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    if data.fecha_inicio < proyecto.fecha_inicio:
        raise HTTPException(status_code=400, detail=f"La fecha de inicio de la tarea ({data.fecha_inicio}) no puede ser anterior a la del proyecto ({proyecto.fecha_inicio})")
    
    if proyecto.fecha_fin and data.fecha_fin and data.fecha_fin > proyecto.fecha_fin:
        raise HTTPException(status_code=400, detail=f"La fecha de fin de la tarea ({data.fecha_fin}) no puede ser posterior a la del proyecto ({proyecto.fecha_fin})")

    tarea = Tarea(**data.model_dump())
    db.add(tarea)
    await db.commit()
    await db.refresh(tarea)
    
    # Reload with relationships for the response
    result = await db.execute(
        select(Tarea)
        .options(
            selectinload(Tarea.estado),
            selectinload(Tarea.prioridad),
            selectinload(Tarea.usuarios).selectinload(TareaUsuario.usuario).selectinload(Usuario.rol),
        )
        .where(Tarea.id_tarea == tarea.id_tarea)
    )
    return result.scalar_one()


@router.put("/{id_tarea}", response_model=TareaOut)
async def update_tarea(
    id_tarea: int,
    data: TareaUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(check_permission("tareas", "puede_editar")),
):
    result = await db.execute(select(Tarea).where(Tarea.id_tarea == id_tarea))
    tarea = result.scalar_one_or_none()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    # Validation if dates are updated
    if data.fecha_inicio or data.fecha_fin:
        result = await db.execute(select(Proyecto).where(Proyecto.id_proyecto == tarea.id_proyecto))
        proyecto = result.scalar_one_or_none()
        if proyecto:
            new_start = data.fecha_inicio or tarea.fecha_inicio
            new_end = data.fecha_fin or tarea.fecha_fin
            
            if new_start < proyecto.fecha_inicio:
                raise HTTPException(status_code=400, detail=f"La fecha de inicio ({new_start}) es anterior a la del proyecto ({proyecto.fecha_inicio})")
            if proyecto.fecha_fin and new_end and new_end > proyecto.fecha_fin:
                raise HTTPException(status_code=400, detail=f"La fecha de fin ({new_end}) es posterior a la del proyecto ({proyecto.fecha_fin})")

    old_estado = tarea.id_estado
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(tarea, field, value)

    if data.id_estado and data.id_estado != old_estado:
        historial = HistorialEstado(
            entidad="tarea",
            id_entidad=id_tarea,
            id_estado_ant=old_estado,
            id_estado_nuevo=data.id_estado,
            id_usuario=current_user.id_usuario,
        )
        db.add(historial)

    await db.commit()
    await db.refresh(tarea)
    
    # Reload with relationships for the response
    result = await db.execute(
        select(Tarea)
        .options(
            selectinload(Tarea.estado),
            selectinload(Tarea.prioridad),
            selectinload(Tarea.usuarios).selectinload(TareaUsuario.usuario).selectinload(Usuario.rol),
        )
        .where(Tarea.id_tarea == id_tarea)
    )
    return result.scalar_one()


@router.delete("/{id_tarea}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tarea(
    id_tarea: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(check_permission("tareas", "puede_eliminar")),
):
    result = await db.execute(select(Tarea).where(Tarea.id_tarea == id_tarea))
    tarea = result.scalar_one_or_none()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    await db.delete(tarea)
    await db.commit()


@router.post("/{id_tarea}/usuarios", status_code=status.HTTP_201_CREATED)
async def assign_usuarios(
    id_tarea: int,
    data: AsignarUsuariosRequest,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(check_permission("tareas", "puede_editar")),
):
    await db.execute(delete(TareaUsuario).where(TareaUsuario.id_tarea == id_tarea))
    for uid in data.id_usuarios:
        db.add(TareaUsuario(id_tarea=id_tarea, id_usuario=uid))
    await db.commit()
    return {"detail": "Usuarios asignados correctamente"}


@router.get("/{id_tarea}/usuarios", response_model=list[int])
async def get_tarea_usuarios(
    id_tarea: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(check_permission("tareas", "puede_ver")),
):
    result = await db.execute(
        select(TareaUsuario.id_usuario).where(TareaUsuario.id_tarea == id_tarea)
    )
    return [row[0] for row in result.all()]
