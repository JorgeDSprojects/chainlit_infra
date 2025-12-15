import chainlit as cl
from src.services.llm_service import llm_service

@cl.on_chat_start
async def start():
    # 1. Definir la configuración del chat (Settings)
    settings = await cl.ChatSettings(
        [
            cl.input_widget.Select(
                id="ModelProvider",
                label="Proveedor de IA",
                values=["ollama", "openai", "openrouter"],
                initial_index=0
            ),
            cl.input_widget.TextInput(
                id="ModelName",
                label="Nombre del Modelo (Opcional)",
                initial="llama3",
                description="Ej: gpt-4, llama3, mistralai/mistral-7b-instruct"
            )
        ]
    ).send()
    
    # Mensaje de bienvenida
    await cl.Message(
        content="¡Sistema listo! Configura el proveedor en el menú de ajustes ⚙️."
    ).send()

@cl.on_message
async def main(message: cl.Message):
    # 1. Recuperar la configuración actual del usuario
    chat_settings = cl.user_session.get("chat_settings")
    
    # Valores por defecto si no ha tocado la configuración
    provider = "ollama"
    model_name = "llama3"
    
    if chat_settings:
        provider = chat_settings.get("ModelProvider", "ollama")
        model_name = chat_settings.get("ModelName", None)

    # 2. Preparar el mensaje de respuesta vacío para hacer streaming
    msg = cl.Message(content="")
    await msg.send()

    # 3. Llamar al servicio y hacer streaming del contenido
    # Usamos 'async for' porque nuestro servicio es un generador asíncrono
    async for token in llm_service.stream_response(
        message=message.content, 
        provider=provider, 
        specific_model=model_name
    ):
        await msg.stream_token(token)
    
    # 4. Finalizar el mensaje
    await msg.update()

@cl.on_settings_update
async def setup_agent(settings):
    # Guardar configuración en la sesión del usuario cuando la cambie
    cl.user_session.set("chat_settings", settings)
    await cl.Message(content=f"✅ Proveedor cambiado a: {settings['ModelProvider']}").send()

