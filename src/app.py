import chainlit as cl
from sqlalchemy.future import select
from src.db.database import async_session
from src.db.models import User
from src.auth.utils import verify_password
from src.services.llm_service import llm_service
from src.db.crud import create_conversation, add_message

# --- CALLBACK DE AUTENTICACIÓN ---
@cl.password_auth_callback
async def auth(username: str, password: str):
    """
    Esta función se llama cuando el usuario intenta loguearse en la UI.
    Devuelve cl.User si es correcto, o None si falla.
    """
    async with async_session() as session:
        # Buscamos al usuario por email
        result = await session.execute(select(User).filter(User.email == username))
        user_db = result.scalars().first()
        
        if user_db and verify_password(password, user_db.hashed_password):
            # CORRECCIÓN 1: Pasar 'id' explícitamente para que coincida con el DataLayer
            return cl.User(
                identifier=username, 
                id=str(user_db.id),  # ¡IMPORTANTE! Esto evita el error 401 en el historial
                metadata={"id": user_db.id}
            )
        
        return None

@cl.on_chat_start
async def start():
    # 1. Recuperar usuario y configuración
    user = cl.user_session.get("user")
    
    # 2. Crear una nueva conversación en la DB si no estamos reanudando una
    async with async_session() as session:
        # Guardamos la conversación inicial
        conv = await create_conversation(session, user_id=user.metadata["id"], title="Nueva Conversación")
        # Guardamos el ID de la conversación en la sesión para usarlo luego
        cl.user_session.set("conversation_id", conv.id)

    # 3. Configuración de Chainlit (Sidebar)
    await cl.ChatSettings(
        [
            cl.input_widget.Select(
                id="ModelProvider",
                label="Proveedor de Modelo",
                values=["ollama", "openai", "anthropic"],
                initial_value="ollama",
                description="Selecciona el proveedor de IA"
            ),
            cl.input_widget.TextInput(
                id="ModelName",
                label="Nombre del Modelo (Opcional)",
                initial_value="",
                placeholder="llama3",
                description="Ej: gpt-4, llama3, mistralai/mistral-7b-instruct"
            )
        ]
    ).send()
    
    await cl.Message(
        content="¡Sistema listo! Configura el proveedor en el menú de ajustes ⚙️."
    ).send()

@cl.on_chat_resume
async def on_chat_resume(conversation):
    """
    Se llama al hacer clic en una conversación antigua del historial.
    Chainlit ya carga los mensajes gracias al DataLayer, aquí solo configuramos contexto.
    """
    user = cl.user_session.get("user")
    # Guardamos el ID de la conversación actual
    cl.user_session.set("conversation_id", conversation["id"])

@cl.on_message
async def main(message: cl.Message):
    # 1. Recuperar la configuración actual
    chat_settings = cl.user_session.get("chat_settings")
    conversation_id = cl.user_session.get("conversation_id")
    user = cl.user_session.get("user")

    # Valores por defecto
    provider = "ollama"
    model_name = "llama3"
    
    if chat_settings:
        provider = chat_settings.get("ModelProvider", "ollama")
        model_name = chat_settings.get("ModelName", None)

    # 2. Guardar el mensaje del usuario en la DB
    if conversation_id:
        async with async_session() as session:
            await add_message(session, conversation_id=int(conversation_id), role="user", content=message.content)

            # CORRECCIÓN 2: Renombrado de conversación compatible con Chainlit nuevo
            # Solo renombramos si es el primer mensaje o la conversación se llama "Nueva Conversación"
            # (Lógica simplificada: renombramos siempre al principio para dar contexto)
            # Recuperamos el hilo actual para actualizarlo
            thread = cl.Thread(id=str(conversation_id))
            thread.name = message.content[:30] + "..."
            await thread.update()

    # 3. Preparar respuesta del asistente
    msg = cl.Message(content="")
    await msg.send()

    full_response = ""

    # 4. Streaming del LLM
    async for token in llm_service.stream_response(
        message=message.content, 
        provider=provider, 
        specific_model=model_name
    ):
        await msg.stream_token(token)
        full_response += token
    
    await msg.update()

    # 5. Guardar respuesta del asistente en la DB
    if conversation_id:
        async with async_session() as session:
            await add_message(session, conversation_id=int(conversation_id), role="assistant", content=full_response)