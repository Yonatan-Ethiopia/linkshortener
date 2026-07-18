from starlette.requests import Request
from sqlmodel import SQLModel, Session, select
from typing import Annotated
from fastapi import Depends, HTTPException, status
from .db import engine
from .models import *

def get_session():
    with Session(engine) as session:
        yield session
        
def get_current_user(request: Request, session: Annotated[Session, Depends(get_session)]):
    unauthorized = HTTPException(
    status_code = status.HTTP_401_UNAUTHORIZED,
    detail = "Authorization error"
    )
    user_id = request.session['user_id']
    if user_id is None:
        raise unauthorized
    user = session.get(userDb, user_id)
    if user is None:
        raise unauthorized
    print("The user is ", user)
    return user
    
