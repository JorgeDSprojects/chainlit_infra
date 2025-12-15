from fastapi import FastAPI
from contextlib import asynccontextmanager
from chainlit.utils import mount_chainlit
from src.config import settings
from src.db.database import engine, Base
from src.routers import users 
# IMPORTANTE: Importar los modelos para que se registren en Base.metadata antes de crear las tablas
import src.db.models 


# --- LIFESPAN (Ciclo de vida) ---
# Esto se ejecuta antes de que la app empiece a recibir peticiones
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crear tablas en la base de datos
    async with engine.begin() as conn:
        # En producción, usarías Alembic para migraciones, pero esto sirve para empezar
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Aquí podrías cerrar conexiones si fuera necesario al apagar

# Iniciamos FastAPI con el lifespan
app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)
app.include_router(users.router, prefix="/api", tags=["Users"]) 
# Endpoint de prueba
@app.get("/api/status")
def read_root():
    return {"status": "ok", "app": settings.APP_NAME, "db": "connected"}

# --- Montar Chainlit ---
mount_chainlit(app=app, target="src/app.py", path="/")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
