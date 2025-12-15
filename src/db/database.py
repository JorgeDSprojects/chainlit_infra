from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# URL de conexión. Para PostgreSQL usarías: postgresql+asyncpg://user:pass@host/db
DATABASE_URL = "sqlite+aiosqlite:///./chat.db"

# Crear el motor de base de datos
engine = create_async_engine(
    DATABASE_URL, 
    echo=True,  # Poner en False en producción (muestra SQL en consola)
    future=True
)

# Fábrica de sesiones
async_session = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Base para nuestros modelos
Base = declarative_base()

# Dependencia para obtener la sesión en los endpoints de FastAPI
async def get_db():
    async with async_session() as session:
        yield session