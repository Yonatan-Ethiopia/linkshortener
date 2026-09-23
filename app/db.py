import os, redis
from sqlmodel import create_engine
from dotenv import load_dotenv

load_dotenv()
database_url = os.getenv("DATABASE_URL", "fg")
if database_url  and database_url .startswith("postgres://"):
    database_url = database_url .replace("postgres://", "postgresql://", 1)
redis_url = os.getenv("REDIS_URL","")

sql_name = "database.db"
sql_url = f"sqlite:///{sql_name}"

engine = create_engine(database_url, echo=True)

redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
