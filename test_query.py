
import asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.models import Proyecto, ProyectoUsuario, Usuario, Cliente, Estado
from app.database import AsyncSessionLocal

async def test():
    try:
        async with AsyncSessionLocal() as db:
            query = select(Proyecto).options(
                selectinload(Proyecto.estado),
                selectinload(Proyecto.cliente).selectinload(Cliente.estado),
            )
            # Simulate Standard User (id_rol=2)
            query = query.join(ProyectoUsuario, Proyecto.id_proyecto == ProyectoUsuario.id_proyecto).where(ProyectoUsuario.id_usuario == 1)
            
            print(f"SQL: {query}")
            result = await db.execute(query)
            projects = result.scalars().all()
            print(f"Projects count: {len(projects)}")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
