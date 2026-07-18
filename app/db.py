import os
from sqlmodel import create_engine

database_url = os.getenv("DATABASE_URL", "fg")

sql_name = "database.db"
sql_url = f"sqlite:///{sql_name}"

engine = create_engine(database_url, echo=True)
