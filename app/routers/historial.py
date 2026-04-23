from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import HistorialEstado, Usuario
from app.schemas.schemas import HistorialOut
from app.auth.auth import get_current_user

router = APIRouter(prefix="/historial", tags=["Historial de Estados"])


@router.get("/{entidad}/{id_entidad}", response_model=list[HistorialOut])
async def get_historial(
    entidad: str,
    id_entidad: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    result = await db.execute(
        select(HistorialEstado)
        .options(
            selectinload(HistorialEstado.estado_ant),
            selectinload(HistorialEstado.estado_nuevo),
        )
        .where(
            HistorialEstado.entidad == entidad,
            HistorialEstado.id_entidad == id_entidad,
        )
        .order_by(HistorialEstado.cambiado_en.desc())
    )
    return result.scalars().all()
