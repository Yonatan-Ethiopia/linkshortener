from fastapi import FastAPI, Depends
from fastapi.responses import RedirectResponse
from sqlmodel import SQLModel, select, Session
from typing import Annotated
import json

from .routers import routers
from . import models
from .models import userDb
from .db import engine
from .dependencies import get_session, auth_rate_limit

from starlette.config import Config
from starlette.requests import Request
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import HTMLResponse, RedirectResponse
from authlib.integrations.starlette_client import OAuth, OAuthError

import os
from dotenv import load_dotenv

load_dotenv()


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

secretkey = os.getenv("SECRET_KEY", "")

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key=secretkey, https_only=True, same_site="lax")

config = Config('.env')
print("CLIENT ID LOADED:", config('GOOGLE_CLIENT_ID'))
oauth = OAuth(config)

CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'

oauth.register(
    name='google',
    server_metadata_url=CONF_URL,
    client_kwargs={
        'scope': 'openid email profile'
    }
)

app.include_router(routers.router)        

    
@app.get('/')
async def homepage(request: Request):
    user = request.session.get('user_id')
    print(user)
    if user:
        data = json.dumps(user)
        html = (
            f'<pre>{data}</pre>'
            '<a href="/logout">logout</a>'
        )
        return HTMLResponse(html)
        print(user)
        return RedirectResponse(url='/dashboard')
    return HTMLResponse('<a href="/login">login</a>')


@app.get('/login')
async def login(request: Request):
    redirect_uri = request.url_for('auth')
    return await oauth.google.authorize_redirect(request, redirect_uri)


@app.get('/auth')
async def auth(request: Request, sess: Annotated[Session, Depends(get_session)], is_allowed: Annotated[bool, Depends(auth_rate_limit)]):
    if not is_allowed:
        raise HTTPException(status_code = 429, detail = "Too many requests")
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as error:
        return HTMLResponse(f'<h1>{error.error}</h1>')
    user_info = token.get('userinfo')
    if user_info:
        user = sess.exec(select(userDb).where(userDb.google_sub == user_info['sub'])).first()
        if user is None:
            user = userDb(
                google_sub=user_info['sub'],
                email = user_info.get('email', ''),
                name = user_info.get('name', ''),
            )
            sess.add(user)
            sess.commit()
            sess.refresh(user)
        
        request.session['user_id'] = user.id
    return RedirectResponse(url='/dashboard')


@app.get('/logout')
async def logout(request: Request):
    request.session.pop('user_id', None)
    return RedirectResponse(url='/')
    

