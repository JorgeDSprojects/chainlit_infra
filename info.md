# Instrucciones para ejecutar el proyecto

# Crea  un entorno virtual 
python -m venv .venv
# Activa el entorno virtual 
.venv\Scripts\activate

# Instala las dependencias
pip install -r requirements.txt

# Ejecuta la aplicación
uvicorn main:app --reload
# Accede a la aplicación en tu navegador
http://localhost:8000/chat

# sie es la primera vez que ejecutas la app, crea un usuario en:
http://localhost:8000/docs
{
  "email": "test@test.com",
  "password": "123"
}
