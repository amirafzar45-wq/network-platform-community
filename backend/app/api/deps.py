from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.security import decode_token
from app.models import User

def current_user(authorization: str = Header(default=''), db: Session = Depends(get_db)) -> User:
    if not authorization.startswith('Bearer '): raise HTTPException(401, 'Authentication required')
    user_id = decode_token(authorization[7:])
    user = db.get(User, user_id)
    if not user: raise HTTPException(401, 'User not found')
    return user
