from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.responses import RedirectResponse
from sqlmodel import SQLModel, create_engine, select, Field, Session, text
from typing import Annotated
import string

from .routers import routers
from . import models
from .db import engine


    


    


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

app = FastAPI()

        
@app.on_event("startup")
def initdb():
    create_db_and_tables()
    
@app.include_router(routers.router)
    

    
    
    

    
    
