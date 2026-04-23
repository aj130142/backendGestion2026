from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.models import Usuario
from app.schemas.schemas import UsuarioCreate, UsuarioUpdate, UsuarioOut
from app.auth.auth import hash_password, check_permission

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


@router.get("/", response_model=list[UsuarioOut])
async def list_usuarios(
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(check_permission("usuarios", "puede_ver")),
):
    result = await db.execute(select(Usuario).options(selectinload(Usuario.rol)))
    return result.scalars().all()


@router.get("/{id_usuario}", response_model=UsuarioOut)
async def get_usuario(
    id_usuario: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(check_permission("usuarios", "puede_ver")),
):
    result = await db.execute(
        select(Usuario)
        .options(selectinload(Usuario.rol))
        .where(Usuario.id_usuario == id_usuario)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


@router.post("/", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
async def create_usuario(
    data: UsuarioCreate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(check_permission("usuarios", "puede_crear")),
):
    existing = await db.execute(select(Usuario).where(Usuario.correo == data.correo))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="El correo ya está registrado")

    user = Usuario(
        nombre=data.nombre,
        correo=data.correo,
        password_hash=hash_password(data.password),
        id_rol=data.id_rol,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Reload with relationships for the response
    result = await db.execute(
        select(Usuario)
        .options(selectinload(Usuario.rol))
        .where(Usuario.id_usuario == user.id_usuario)
    )
    return result.scalar_one()


@router.put("/{id_usuario}", response_model=UsuarioOut)
async def update_usuario(
    id_usuario: int,
    data: UsuarioUpdate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(check_permission("usuarios", "puede_editar")),
):
    result = await db.execute(select(Usuario).where(Usuario.id_usuario == id_usuario))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if data.nombre is not None:
        user.nombre = data.nombre
    if data.correo is not None:
        user.correo = data.correo
    if data.password is not None:
        user.password_hash = hash_password(data.password)
    if data.id_rol is not None:
        user.id_rol = data.id_rol
    if data.activo is not None:
        user.activo = data.activo

    await db.commit()
    await db.refresh(user)
    
    # Reload with relationships for the response
    result = await db.execute(
        select(Usuario)
        .options(selectinload(Usuario.rol))
        .where(Usuario.id_usuario == id_usuario)
    )
    return result.scalar_one()


@router.delete("/{id_usuario}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_usuario(
    id_usuario: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(check_permission("usuarios", "puede_eliminar")),
):
    result = await db.execute(select(Usuario).where(Usuario.id_usuario == id_usuario))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    await db.delete(user)
    await db.commit()
