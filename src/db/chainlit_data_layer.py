import chainlit as cl
import chainlit.data as cl_data
from chainlit.types import ThreadDict, ThreadFilter, Pagination, Feedback, PaginatedResponse, PageInfo
from sqlalchemy.future import select
from sqlalchemy import delete
from src.db.database import async_session
from src.db.models import User, Conversation, Message
from src.db.crud import create_conversation, add_message

class CustomDataLayer(cl_data.BaseDataLayer):
    async def get_user(self, identifier: str):
        """
        Recupera el usuario de la DB cuando se recarga la sesión.
        CRÍTICO: Debe devolver metadata con el ID para que app.py no falle.
        """
        async with async_session() as session:
            result = await session.execute(select(User).filter(User.email == identifier))
            user_db = result.scalars().first()
            
            if user_db:
                return cl.PersistedUser(
                    id=str(user_db.id),
                    identifier=user_db.email,
                    createdAt=user_db.created_at.isoformat() if user_db.created_at else None,
                    metadata={"id": user_db.id} # ¡ESTO ES LO QUE FALTABA PARA EL ERROR KEYERROR 'ID'!
                )
            return None

    async def create_user(self, user: cl.User): 
        pass

    async def get_thread(self, thread_id: str):
        """Recupera una conversación completa."""
        async with async_session() as session:
            try:
                t_id = int(thread_id)
            except ValueError:
                return None

            result = await session.execute(select(Conversation).filter(Conversation.id == t_id))
            conversation = result.scalars().first()
            if not conversation:
                return None

            msgs_result = await session.execute(
                select(Message)
                .filter(Message.conversation_id == t_id)
                .order_by(Message.created_at.asc())
            )
            db_messages = msgs_result.scalars().all()

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
        
        # Objeto PageInfo completo para evitar ValidationError
        empty_page_info = PageInfo(
            hasNextPage=False, 
            hasPreviousPage=False, 
            startCursor=None, 
            endCursor=None
        )

        if not filter.userId:
            return PaginatedResponse(data=[], pageInfo=empty_page_info)

        async with async_session() as session:
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
                    "steps": [],
                    "metadata": {}
                })

            return PaginatedResponse(
                data=threads, 
                pageInfo=empty_page_info # ¡SOLUCIÓN AL VALIDATION ERROR!
            )

    async def update_thread(self, thread_id: str, name: str = None, user_id: str = None, metadata: dict = None, tags: list = None):
        if name:
             try:
                 t_id = int(thread_id)
             except ValueError:
                 return

             async with async_session() as session:
                result = await session.execute(select(Conversation).filter(Conversation.id == t_id))
                conversation = result.scalars().first()
                if conversation:
                    conversation.title = name
                    await session.commit()

    async def delete_thread(self, thread_id: str):
        try:
             t_id = int(thread_id)
        except ValueError:
             return

        async with async_session() as session:
            await session.execute(delete(Conversation).filter(Conversation.id == t_id))
            await session.commit()
    
    async def get_thread_author(self, thread_id: str):
         try:
             t_id = int(thread_id)
         except ValueError:
             return ""

         async with async_session() as session:
            result = await session.execute(select(Conversation).filter(Conversation.id == t_id))
            conversation = result.scalars().first()
            if conversation:
                 return str(conversation.user_id)
            return ""

    # --- MÉTODOS OBLIGATORIOS (STUBS) ---
    async def create_step(self, step_dict: dict): pass 
    async def update_step(self, step_dict: dict): pass
    async def delete_step(self, step_id: str): pass
    async def get_element(self, thread_id: str, element_id: str): pass
    async def create_element(self, element_dict: dict): pass
    async def delete_element(self, element_id: str): pass
    async def upsert_feedback(self, feedback: Feedback): pass
    async def delete_feedback(self, feedback_id: str): pass
    async def build_debug_url(self): pass
    async def close(self): pass