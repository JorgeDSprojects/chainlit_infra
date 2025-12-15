import chainlit as cl
from sqlalchemy.future import select
from src.db.database import async_session
from src.db.models import User
from src.db.crud import create_conversation, add_message, get_conversation_history
from src.auth.utils import verify_password
from src.services.llm_service import llm_service
from src.services.ollama_service import get_ollama_models

# --- CALLBACK DE AUTENTICACIÓN ---
@cl.password_auth_callback
async def auth(username: str, password: str):
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.email == username))
        user_db = result.scalars().first()
        if user_db and verify_password(password, user_db.hashed_password):
            return cl.User(identifier=username, metadata={"id": user_db.id})
        return None

# --- CHAT START ---
@cl.on_chat_start
async def start():
    user = cl.user_session.get("user")
    
    # 1. Comprobar si estamos reanudando un chat (thread_id viene en la URL/contexto)
    thread_id = None
    if cl.context.session.thread_id:
        thread_id = cl.context.session.thread_id

    # Recuperamos modelos de Ollama dinámicamente
    ollama_models = await get_ollama_models()
    
    # 2. Si es un chat nuevo (no hay thread_id previo en la UI de Chainlit), creamos uno
    if not thread_id:
        async with async_session() as session:
            # Título temporal, luego podríamos generarlo con IA
            conv = await create_conversation(session, user_id=user.metadata["id"], title="Nueva Conversación")
            cl.user_session.set("conversation_id", conv.id)
            # Forzamos el ID del hilo en Chainlit para que coincida con nuestra DB
            cl.context.session.thread_id = str(conv.id) 
            # Inicializar historial vacío
            cl.user_session.set("message_history", [])
    else:
        # 3. Si estamos REANUDANDO
        cl.user_session.set("conversation_id", int(thread_id))
        
        # Cargar historial de la DB para el contexto del LLM
        async with async_session() as session:
            db_messages = await get_conversation_history(session, int(thread_id))
            history = [{"role": m.role, "content": m.content} for m in db_messages]
            cl.user_session.set("message_history", history)
            
        await cl.Message(f"♻️ Conversación #{thread_id} restaurada.").send()

    # 4. Configuración (Ahora con lista dinámica de Ollama)
    settings = await cl.ChatSettings(
        [
            cl.input_widget.Select(
                id="ModelProvider",
                label="Proveedor",
                values=["ollama", "openai", "openrouter"],
                initial_index=0
            ),
            # El campo de modelo ahora es un Select si es Ollama, o texto si es otro
            # Para simplificar, usamos un Select con los de Ollama + opción 'custom'
            cl.input_widget.Select(
                id="ModelName",
                label="Modelo (Ollama Detectado)",
                values=ollama_models + ["gpt-3.5-turbo", "gpt-4"],
                initial_index=0
            )
        ]
    ).send()

@cl.on_message
async def main(message: cl.Message):
    conversation_id = cl.user_session.get("conversation_id")
    history = cl.user_session.get("message_history")
    
    # ... (Recuperar settings igual que antes) ...
    chat_settings = cl.user_session.get("chat_settings")
    provider = chat_settings.get("ModelProvider", "ollama") if chat_settings else "ollama"
    model_name = chat_settings.get("ModelName", "llama3")

    # Guardar User Msg
    history.append({"role": "user", "content": message.content})
    async with async_session() as session:
        await add_message(session, conversation_id, "user", message.content)

    msg = cl.Message(content="")
    await msg.send()
    
    full_response = ""
    async for token in llm_service.stream_response(history, provider, model_name):
        await msg.stream_token(token)
        full_response += token
    
    await msg.update()
    
    # Guardar Assistant Msg
    history.append({"role": "assistant", "content": full_response})
    async with async_session() as session:
        await add_message(session, conversation_id, "assistant", full_response)
        
    # Actualizar el título del chat si es el primer mensaje
    if len(history) <= 2:
        await cl.rename_thread(thread_id=str(conversation_id), name=message.content[:30] + "...")
