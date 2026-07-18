from fastapi import FastAPI
from sqlmodel import SQLModel

from .routers import routers
from . import models
from .db import engine

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

app = FastAPI()

app.include_router(routers.router)        
@app.on_event("startup")
def initdb():
    create_db_and_tables()
    

