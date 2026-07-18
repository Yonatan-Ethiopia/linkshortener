from sqlmodel import SQLModel, Session, select
from typing import Annotated
from fastapi import Depends
from .db import engine
from .models import *

def get_session():
    with Session(engine) as session:
        yield session
        
def get_current_user( session: Annotated[Session, Depends(get_session)]):
    user = session.exec(select(userDb)).first()
    print("The user is ", user)
    return user
    
