from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.database import get_db
from src.db.models import User
from src.auth.utils import get_password_hash

router = APIRouter()

# Schema para recibir datos (Pydantic)
class UserCreate(BaseModel):
    email: str
    password: str

@router.post("/register")
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # 1. Verificar si el usuario ya existe
    result = await db.execute(select(User).filter(User.email == user.email))
    existing_user = result.scalars().first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    # 2. Crear usuario con contraseña hasheada
    hashed_pwd = get_password_hash(user.password)
    new_user = User(email=user.email, hashed_password=hashed_pwd)
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return {"message": "Usuario creado correctamente", "id": new_user.id, "email": new_user.email}