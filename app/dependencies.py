from starlette.requests import Request
from sqlmodel import SQLModel, Session, select
from typing import Annotated
from fastapi import Depends, HTTPException, status
from urllib.parse import urlparse
from .db import engine
from .models import *
import redis,os
from dotenv import load_dotenv
from .db import redis_client

def get_session():
    with Session(engine) as session:
        yield session
        
def get_current_user(request: Request, session: Annotated[Session, Depends(get_session)]):
    unauthorized = HTTPException(
    status_code = status.HTTP_401_UNAUTHORIZED,
    detail = "Authorization error"
    )
    try:
        user_id = request.session['user_id']
        if user_id is None:
            raise unauthorized
        user = session.get(userDb, user_id)
        if user is None:
            raise unauthorized
        print("The user is ", user)
        return user
    except Exception as e:
        raise unauthorized

def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme:
        url = "https://" + url
        parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise HTTPException(status_code=400, detail="Invalid URL")
    return url

def create_rate_limit( request: Request ):
    user_id = request.session["user_id"]
    if user_id is None:
        return False
    key = f"ratelimit:user:{user_id}:/create"
    print(f"{user_id} wants to make create a link")
    return rate_limit(key, limit = 5, window_size = 60)
    
def auth_rate_limit( request: Request )-> bool:
    ip = request.client.host
    if ip is None:
        return False
    key = f"ratelimit:ip:{ip}:/auth"
    return rate_limit(key, limit = 5, window_size = 60)

    
def rate_limit(key: str, limit: int, window_size: int)-> bool:
    current = redis_client.incr(key)
    if current == 1:
        redis_client.expire(key, window_size)
    print(f"{key} is at their {current} th request")
    return current < limit
    
