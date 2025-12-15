from fastapi import FastAPI
from chainlit.utils import mount_chainlit
from src.config import settings

app = FastAPI(title=settings.APP_NAME)

# Endpoint de API normal (para demostrar que FastAPI funciona independientemente)
@app.get("/api/status")
def read_root():
    return {"status": "ok", "app": settings.APP_NAME}

# --- Montar Chainlit ---
# target: ruta relativa al archivo donde está la lógica de chainlit
# path: la URL donde quieres ver el chat (ej: /chat o la raíz /)
mount_chainlit(app=app, target="src/app.py", path="/")


if __name__ == "__main__":
    import uvicorn
    # Se recomienda usar reload=True solo en desarrollo
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
