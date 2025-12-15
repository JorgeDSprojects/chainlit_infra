from fastapi import FastAPI
from fastapi.responses import RedirectResponse # <--- Importamos esto para redirigir
from contextlib import asynccontextmanager
from chainlit.utils import mount_chainlit
from src.config import settings
from src.db.database import engine, Base
from src.routers import users
import src.db.models 
from src.db.chainlit_data_layer import CustomDataLayer
import chainlit.data as cl_data

# --- LIFESPAN (Ciclo de vida) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crear tablas en la base de datos
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Cerrar conexiones al apagar
    await engine.dispose()

# Iniciamos FastAPI
app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)
app.include_router(users.router, prefix="/api", tags=["Users"]) 

# Endpoint de estado
@app.get("/api/status")
def read_root():
    return {"status": "ok", "app": settings.APP_NAME, "db": "connected"}

# --- NUEVO: REDIRECCIÓN DE RAÍZ ---
# Si el usuario entra a http://localhost:8000/, lo mandamos directo al chat
@app.get("/")
def root():
    return RedirectResponse(url="/chat")

# --- ACTIVAR DATA LAYER ---
# Esto le dice a Chainlit que use nuestra clase para leer la DB
cl_data._data_layer = CustomDataLayer()

# --- Montar Chainlit ---
mount_chainlit(app=app, target="src/app.py", path="/chat")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)