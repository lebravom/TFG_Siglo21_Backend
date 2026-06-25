from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, async_sessionmaker
from typing import AsyncGenerator

# 1. URL con driver asíncrono para SQLite
DATABASE_URL = "sqlite+aiosqlite:///./mediciones.db"

# 2. Crear el motor asíncrono
engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=True,  # opcional: logs de SQL
    connect_args={"check_same_thread": False}  # necesario para SQLite
)




# 3. Fábrica de sesiones asíncronas
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# 4. Generador de sesión para inyección de dependencias (FastAPI)
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session