from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import Usuario, TokenRevocado
from app.schemas.schemas import LoginRequest, TokenResponse, UsuarioOut
from app.auth.auth import verify_password, create_access_token, get_current_user, decode_token
from app.limiter import limiter

router = APIRouter(prefix="/auth", tags=["Autenticación"])
bearer_scheme = HTTPBearer()


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, data: LoginRequest, db: AsyncSession = Depends(get_db)):
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
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """(#6b) Logout completo: revoca el token actual del usuario.
    El token se agrega a la tabla de tokens revocados para invalidarlo."""
    token = credentials.credentials

    # Verificar si ya fue revocado
    existing = await db.execute(
        select(TokenRevocado).where(TokenRevocado.token == token)
    )
    if existing.scalar_one_or_none():
        return  # Ya estaba revocado

    revoked = TokenRevocado(token=token, id_usuario=current_user.id_usuario)
    db.add(revoked)
    await db.commit()


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
    import jwt
    from app.config import settings
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM],
            audience="techsolutions-frontend", issuer="techsolutions-api",
        )
        user_id = int(payload.get("sub", 0))
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")

    revoked = TokenRevocado(token=token, id_usuario=user_id)
    db.add(revoked)
    await db.commit()


@router.get("/me", response_model=UsuarioOut)
async def get_me(current_user: Usuario = Depends(get_current_user)):
    return current_user
