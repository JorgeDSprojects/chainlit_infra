from openai import AsyncOpenAI
from src.config import settings

class LLMService:
    # ... (El método __init__ y _get_client_and_model se quedan igual) ...
    def __init__(self):
        pass

    def _get_client_and_model(self, provider: str):
        # ... (copia tu código existente de la Fase 2 aquí) ...
        if provider == "ollama":
            return AsyncOpenAI(base_url=settings.OLLAMA_BASE_URL, api_key="ollama"), "llama3"
        elif provider == "openrouter":
            return AsyncOpenAI(base_url="[https://openrouter.ai/api/v1](https://openrouter.ai/api/v1)", api_key=settings.OPENROUTER_API_KEY), "openai/gpt-3.5-turbo"
        elif provider == "openai":
            return AsyncOpenAI(api_key=settings.OPENAI_API_KEY), "gpt-3.5-turbo"
        else:
            raise ValueError(f"Proveedor desconocido: {provider}")

    # --- CAMBIO IMPORTANTE AQUÍ ---
    async def stream_response(self, history: list, provider: str, specific_model: str = None):
        """
        Ahora recibe 'history' (lista de mensajes) en lugar de solo un string.
        """
        client, default_model = self._get_client_and_model(provider)
        model = specific_model if specific_model else default_model

        # Añadimos un System Prompt al inicio del historial
        system_message = {"role": "system", "content": "Eres un asistente útil y amable."}
        full_messages = [system_message] + history

        try:
            stream = await client.chat.completions.create(
                model=model,
                messages=full_messages,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            yield f"\n\n**Error al conectar con {provider}:** {str(e)}"

llm_service = LLMService()
