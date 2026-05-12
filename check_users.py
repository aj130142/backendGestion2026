
import asyncio
from app.database import AsyncSessionLocal
from sqlalchemy import text

async def main():
    try:
        async with AsyncSessionLocal() as db:
            res = await db.execute(text('SELECT id_usuario, nombre, id_rol FROM usuarios'))
            print(res.all())
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
