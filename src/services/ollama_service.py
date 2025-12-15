import httpx
from src.config import settings

async def get_ollama_models():
    """Consulta la API de Ollama para obtener modelos disponibles."""
    try:
        # La URL base suele ser http://localhost:11434/v1, pero la API de tags está en /api/tags
        # Ajustamos la URL base quitando el /v1 si existe
        base_url = settings.OLLAMA_BASE_URL.replace("/v1", "")
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                # Extraemos solo los nombres de los modelos
                return [model["name"] for model in data.get("models", [])]
    except Exception as e:
        print(f"Error conectando con Ollama: {e}")
    
    # Fallback si falla
    return ["llama3", "mistral"]