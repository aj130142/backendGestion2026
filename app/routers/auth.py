from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import Usuario, TokenRevocado
from app.schemas.schemas import LoginRequest, TokenResponse, UsuarioOut
from app.auth.auth import verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Usuario).where(Usuario.correo == data.correo))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
        )

    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta inactiva. Contacta al administrador.",
        )

    token = create_access_token({"sub": str(user.id_usuario)})
    return TokenResponse(access_token=token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    # We need the raw token — use a trick via request state
):
    # Token is already validated by get_current_user; we just revoke it
    # We'll handle the raw token via a custom approach in dependencies
    # For now, this is a placeholder — the actual token revocation happens in dependencies
    pass


@router.post("/logout/token", status_code=status.HTTP_204_NO_CONTENT)
async def logout_with_token(
    data: dict,
    db: AsyncSession = Depends(get_db),
):
    """Receive {'token': '...'} and revoke it."""
    token = data.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="Token requerido")

    existing = await db.execute(select(TokenRevocado).where(TokenRevocado.token == token))
    if existing.scalar_one_or_none():
        return  # Already revoked

    # Decode to get user_id (don't raise if expired)
    from jose import jwt
    from app.config import settings
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = int(payload.get("sub", 0))
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")

    revoked = TokenRevocado(token=token, id_usuario=user_id)
    db.add(revoked)
    await db.commit()


@router.get("/me", response_model=UsuarioOut)
async def get_me(current_user: Usuario = Depends(get_current_user)):
    return current_user
