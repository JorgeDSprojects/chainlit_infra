from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import Conversation, Message

async def create_conversation(db: AsyncSession, user_id: int, title: str = "Nueva Conversación"):
    """Crea una nueva entrada de conversación."""
    db_conversation = Conversation(user_id=user_id, title=title)
    db.add(db_conversation)
    await db.commit()
    await db.refresh(db_conversation)
    return db_conversation

async def add_message(db: AsyncSession, conversation_id: int, role: str, content: str):
    """Guarda un mensaje en una conversación específica."""
    db_message = Message(conversation_id=conversation_id, role=role, content=content)
    db.add(db_message)
    await db.commit()
    await db.refresh(db_message)
    return db_message

async def get_conversation_history(db: AsyncSession, conversation_id: int):
    """Recupera todos los mensajes de una conversación."""
    result = await db.execute(
        select(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    return result.scalars().all()