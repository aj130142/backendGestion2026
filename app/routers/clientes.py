from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.models import Cliente, HistorialEstado, Usuario
from app.schemas.schemas import ClienteCreate, ClienteUpdate, ClienteOut
from app.auth.auth import check_permission, get_current_user

router = APIRouter(prefix="/clientes", tags=["Clientes"])


@router.get("/", response_model=list[ClienteOut])
async def list_clientes(
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(check_permission("clientes", "puede_ver")),
):
    result = await db.execute(
        select(Cliente).options(selectinload(Cliente.estado))
    )
    return result.scalars().all()


@router.get("/{id_cliente}", response_model=ClienteOut)
async def get_cliente(
    id_cliente: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(check_permission("clientes", "puede_ver")),
):
    result = await db.execute(
        select(Cliente)
        .options(selectinload(Cliente.estado))
        .where(Cliente.id_cliente == id_cliente)
    )
    cliente = result.scalar_one_or_none()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente


@router.post("/", response_model=ClienteOut, status_code=status.HTTP_201_CREATED)
async def create_cliente(
    data: ClienteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(check_permission("clientes", "puede_crear")),
):
    cliente = Cliente(**data.model_dump())
    db.add(cliente)
    await db.commit()
    await db.refresh(cliente)
    
    # Reload with relationships for the response
    result = await db.execute(
        select(Cliente)
        .options(selectinload(Cliente.estado))
        .where(Cliente.id_cliente == cliente.id_cliente)
    )
    return result.scalar_one()


@router.put("/{id_cliente}", response_model=ClienteOut)
async def update_cliente(
    id_cliente: int,
    data: ClienteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(check_permission("clientes", "puede_editar")),
):
    result = await db.execute(select(Cliente).where(Cliente.id_cliente == id_cliente))
    cliente = result.scalar_one_or_none()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    old_estado = cliente.id_estado
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(cliente, field, value)

    # Track state change
    if data.id_estado and data.id_estado != old_estado:
        historial = HistorialEstado(
            entidad="cliente",
            id_entidad=id_cliente,
            id_estado_ant=old_estado,
            id_estado_nuevo=data.id_estado,
            id_usuario=current_user.id_usuario,
        )
        db.add(historial)

    await db.commit()
    await db.refresh(cliente)
    
    # Reload with relationships for the response
    result = await db.execute(
        select(Cliente)
        .options(selectinload(Cliente.estado))
        .where(Cliente.id_cliente == id_cliente)
    )
    return result.scalar_one()


@router.delete("/{id_cliente}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cliente(
    id_cliente: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(check_permission("clientes", "puede_eliminar")),
):
    result = await db.execute(select(Cliente).where(Cliente.id_cliente == id_cliente))
    cliente = result.scalar_one_or_none()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    await db.delete(cliente)
    await db.commit()
