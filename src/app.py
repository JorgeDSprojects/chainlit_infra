import chainlit as cl
from sqlalchemy.future import select
from src.db.database import async_session
from src.db.models import User
from src.db.crud import create_conversation, add_message
from src.auth.utils import verify_password
from src.services.llm_service import llm_service

# --- AUTENTICACIÓN (Igual que Fase 4) ---
@cl.password_auth_callback
async def auth(username: str, password: str):
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.email == username))
        user_db = result.scalars().first()
        if user_db and verify_password(password, user_db.hashed_password):
            return cl.User(identifier=username, metadata={"id": user_db.id})
        return None

@cl.on_chat_start
async def start():
    user = cl.user_session.get("user")
    
    # 1. Crear una nueva conversación en la Base de Datos
    async with async_session() as session:
        conversation = await create_conversation(session, user_id=user.metadata["id"])
        # Guardamos el ID de la conversación en la sesión para usarlo luego
        cl.user_session.set("conversation_id", conversation.id)

    # 2. Inicializar el historial en memoria (para el contexto inmediato)
    cl.user_session.set("message_history", [])

    if user:
        await cl.Message(f"Hola {user.identifier}. Conversación #{conversation.id} iniciada.").send()

    # Settings del Chat
    await cl.ChatSettings([
        cl.input_widget.Select(id="ModelProvider", label="Proveedor", values=["ollama", "openai", "openrouter"], initial_index=0),
        cl.input_widget.TextInput(id="ModelName", label="Modelo", initial="llama3")
    ]).send()

@cl.on_message
async def main(message: cl.Message):
    # Recuperar datos de la sesión
    conversation_id = cl.user_session.get("conversation_id")
    history = cl.user_session.get("message_history")
    chat_settings = cl.user_session.get("chat_settings")
    
    provider = chat_settings.get("ModelProvider", "ollama") if chat_settings else "ollama"
    model_name = chat_settings.get("ModelName", None)

    # 1. Añadir mensaje del USUARIO al historial y a la DB
    history.append({"role": "user", "content": message.content})
    
    async with async_session() as session:
        await add_message(session, conversation_id, "user", message.content)

    # 2. Preparar respuesta del Asistente
    msg = cl.Message(content="")
    await msg.send()
    
    full_response = ""

    # 3. Llamar al LLM pasando TODO el historial
    async for token in llm_service.stream_response(history, provider, model_name):
        await msg.stream_token(token)
        full_response += token
    
    # 4. Actualizar UI y guardar respuesta del ASISTENTE en DB
    await msg.update()
    
    history.append({"role": "assistant", "content": full_response})
    
    async with async_session() as session:
        await add_message(session, conversation_id, "assistant", full_response)


@cl.on_settings_update
async def setup_agent(settings):
    cl.user_session.set("chat_settings", settings)
    await cl.Message(content=f"✅ Proveedor cambiado a: {settings['ModelProvider']}").send()

