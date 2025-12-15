from fastapi import FastAPI
from contextlib import asynccontextmanager
from chainlit.utils import mount_chainlit
from src.config import settings
from src.db.database import engine, Base
from src.routers import users
import src.db.models 

# --- LIFESPAN (Ciclo de vida) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicio: Crear tablas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Cierre: Liberar conexiones (SOLUCIONA EL BLOQUEO AL CERRAR)
    await engine.dispose()

# Iniciamos FastAPI
app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

# Registrar rutas
app.include_router(users.router, prefix="/api", tags=["Users"])

# Montar Chainlit
mount_chainlit(app=app, target="src/app.py", path="/chat")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
