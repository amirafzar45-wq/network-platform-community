from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.security import hash_password, verify_password, create_token
from app.models import User
from app.schemas.schemas import RegisterIn, LoginIn, TokenOut

router = APIRouter(prefix='/auth', tags=['auth'])

@router.post('/register', response_model=TokenOut)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    count = db.scalar(select(func.count(User.id))) or 0
    if count > 0: raise HTTPException(403, 'Initial administrator already exists')
    user = User(username=data.username, password_hash=hash_password(data.password))
    db.add(user); db.commit(); db.refresh(user)
    return TokenOut(access_token=create_token(user.id))

@router.post('/login', response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == data.username))
    if not user or not verify_password(data.password, user.password_hash): raise HTTPException(401, 'Invalid credentials')
    return TokenOut(access_token=create_token(user.id))
