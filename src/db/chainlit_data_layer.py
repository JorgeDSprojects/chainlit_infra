import chainlit as cl
import chainlit.data as cl_data
# CORRECCIÓN: Importar Pagination desde chainlit.types
from chainlit.types import ThreadDict, ThreadFilter, Pagination, Feedback
from sqlalchemy.future import select
from sqlalchemy import delete
from src.db.database import async_session
from src.db.models import User, Conversation, Message
from src.db.crud import create_conversation, add_message

class CustomDataLayer(cl_data.BaseDataLayer):
    async def get_user(self, identifier: str):
        # Ya manejamos esto en el auth callback, pero es parte de la interfaz
        async with async_session() as session:
            result = await session.execute(select(User).filter(User.email == identifier))
            return result.scalars().first()

    async def create_user(self, user: cl.User): 
        # No usamos este método porque tenemos registro propio, pero debe existir
        pass

    # --- GESTIÓN DE THREADS (Conversaciones) ---

    async def get_thread(self, thread_id: str):
        """Recupera una conversación completa para mostrarla."""
        async with async_session() as session:
            # 1. Buscar la conversación
            result = await session.execute(select(Conversation).filter(Conversation.id == int(thread_id)))
            conversation = result.scalars().first()
            if not conversation:
                return None

            # 2. Buscar sus mensajes
            msgs_result = await session.execute(
                select(Message)
                .filter(Message.conversation_id == int(thread_id))
                .order_by(Message.created_at.asc())
            )
            db_messages = msgs_result.scalars().all()

            # 3. Formatear para Chainlit
            steps = []
            for msg in db_messages:
                steps.append({
                    "id": str(msg.id),
                    "type": "user_message" if msg.role == "user" else "assistant_message",
                    "content": msg.content,
                    "createdAt": msg.created_at.isoformat() if msg.created_at else None,
                })

            return {
                "id": str(conversation.id),
                "createdAt": conversation.created_at.isoformat() if conversation.created_at else None,
                "name": conversation.title,
                "userId": str(conversation.user_id),
                "steps": steps,
                "metadata": {} 
            }

    async def list_threads(self, pagination: Pagination, filter: ThreadFilter):
        """Lista las conversaciones en la barra lateral."""
        if not filter.userId:
            return cl_data.PaginatedResponse(data=[], hasMore=False)

        async with async_session() as session:
            # Consulta básica paginada
            stmt = (
                select(Conversation)
                .filter(Conversation.user_id == int(filter.userId))
                .order_by(Conversation.created_at.desc())
                .limit(pagination.first)
            )
            
            result = await session.execute(stmt)
            conversations = result.scalars().all()

            threads = []
            for conv in conversations:
                threads.append({
                    "id": str(conv.id),
                    "createdAt": conv.created_at.isoformat() if conv.created_at else None,
                    "name": conv.title,
                    "userId": str(conv.user_id),
                    "steps": [], # No necesitamos cargar mensajes para la lista
                    "metadata": {}
                })

            return cl_data.PaginatedResponse(data=threads, hasMore=False)

    async def update_thread(self, thread_id: str, name: str = None, user_id: str = None, metadata: dict = None, tags: list = None):
        """Actualiza el nombre del hilo."""
        if name:
             async with async_session() as session:
                result = await session.execute(select(Conversation).filter(Conversation.id == int(thread_id)))
                conversation = result.scalars().first()
                if conversation:
                    conversation.title = name
                    await session.commit()

    async def delete_thread(self, thread_id: str):
        """Borra una conversación."""
        async with async_session() as session:
            await session.execute(delete(Conversation).filter(Conversation.id == int(thread_id)))
            await session.commit()
    
    async def get_thread_author(self, thread_id: str):
         async with async_session() as session:
            result = await session.execute(select(Conversation).filter(Conversation.id == int(thread_id)))
            conversation = result.scalars().first()
            if conversation:
                 return str(conversation.user_id)
            return ""

    # --- MÉTODOS OBLIGATORIOS (Aunque no los usemos todos aún) ---

    async def create_step(self, step_dict: dict):
        pass 

    async def update_step(self, step_dict: dict):
        pass

    async def delete_step(self, step_id: str):
        pass

    async def get_element(self, thread_id: str, element_id: str):
        pass

    async def create_element(self, element_dict: dict):
        pass
    
    async def delete_element(self, element_id: str):
        pass

    async def upsert_feedback(self, feedback: Feedback):
        pass

    async def delete_feedback(self, feedback_id: str):
        pass

    async def build_debug_url(self):
        pass

    async def close(self):
        pass