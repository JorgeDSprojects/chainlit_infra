from openai import AsyncOpenAI
from src.config import settings

class LLMService:
    def __init__(self):
        # Inicializamos los clientes. 
        # Nota: En producción, podrías usar Singleton o Inyección de Dependencias.
        pass

    def _get_client_and_model(self, provider: str):
        """
        Devuelve el cliente configurado y el nombre del modelo por defecto 
        según el proveedor seleccionado.
        """
        if provider == "ollama":
            # Ollama corre localmente (o en Docker mapeado a localhost)
            return AsyncOpenAI(
                base_url=settings.OLLAMA_BASE_URL, 
                api_key="ollama" # Requerido por la librería, pero ignorado por Ollama
            ), "llama3" # Asegúrate de haber hecho 'ollama pull llama3' en tu contenedor
            
        elif provider == "openrouter":
            # OpenRouter
            return AsyncOpenAI(
                base_url="[https://openrouter.ai/api/v1](https://openrouter.ai/api/v1)",
                api_key=settings.OPENROUTER_API_KEY
            ), "openai/gpt-3.5-turbo" # Modelo default de OpenRouter
            
        elif provider == "openai":
            # OpenAI Oficial
            return AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY
            ), "gpt-3.5-turbo"
            
        else:
            raise ValueError(f"Proveedor desconocido: {provider}")

    async def stream_response(self, message: str, provider: str, specific_model: str = None):
        """
        Genera una respuesta en streaming.
        """
        client, default_model = self._get_client_and_model(provider)
        
        # Si la UI nos manda un modelo específico, lo usamos, si no, el default
        model = specific_model if specific_model else default_model

        # Mensajes básicos (En la Fase 5 meteremos el historial real aquí)
        messages = [
            {"role": "system", "content": "Eres un asistente útil y conciso."},
            {"role": "user", "content": message}
        ]

        try:
            stream = await client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            yield f"\n\n**Error al conectar con {provider}:** {str(e)}"

# Instancia global para usar en app.py
llm_service = LLMService()