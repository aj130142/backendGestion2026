from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.models import Usuario, TokenRevocado, RolPermiso, Modulo

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer()


# ─── Password helpers ────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ─── JWT helpers ─────────────────────────────────────────────────────────────

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ─── Dependencies ─────────────────────────────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Usuario:
    token = credentials.credentials

    # Check blacklist
    result = await db.execute(
        select(TokenRevocado).where(TokenRevocado.token == token)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token revocado. Por favor inicia sesión nuevamente.",
        )

    payload = decode_token(token)
    user_id: Optional[int] = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

    result = await db.execute(
        select(Usuario)
        .options(selectinload(Usuario.rol))
        .where(Usuario.id_usuario == int(user_id))
    )
    user = result.scalar_one_or_none()

    if not user or not user.activo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado o inactivo")

    return user


def check_permission(modulo_nombre: str, accion: str):
    """
    Returns a dependency that checks if the current user's role has the required
    permission for the given module and action (puede_ver, puede_crear, etc.)
    """
    async def dependency(
        current_user: Usuario = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        # Fetch module id
        mod_result = await db.execute(
            select(Modulo).where(Modulo.nombre == modulo_nombre)
        )
        modulo = mod_result.scalar_one_or_none()
        if not modulo:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Módulo '{modulo_nombre}' no encontrado")

        # Fetch permission for this role + module
        perm_result = await db.execute(
            select(RolPermiso).where(
                RolPermiso.id_rol == current_user.id_rol,
                RolPermiso.id_modulo == modulo.id_modulo,
            )
        )
        permiso = perm_result.scalar_one_or_none()

        if not permiso or not getattr(permiso, accion, False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No tienes permiso para '{accion}' en el módulo '{modulo_nombre}'",
            )
        return current_user

    return dependency
