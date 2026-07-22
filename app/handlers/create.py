from fastapi import Request, Response, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse, FileResponse
from sqlmodel import SQLModel, create_engine, select, Field, Session, text, func

from typing import Annotated
from fastapi.templating import Jinja2Templates
from sqlalchemy.schema import Sequence

from ..dependencies import get_session, get_current_user, normalize_url, auth_rate_limit, create_rate_limit, does_hash_exist, does_username_exist
from ..internals.encoders import encode_to_base62, decode_from_base62
from ..models import *
from ..db import engine

import logging

# Set up logger
logger = logging.getLogger(__name__)


def create_link(request: Request, curr_user: currUser, url: UrlReqCreate):
    
    try:
        with Session(engine) as session:
            full_url = url.fullurl
            full_url = normalize_url(full_url)
            if full_url is not None:
                url.fullurl = full_url
                if url.link_username and not url.link_username.strip():
                    url.link_username = None
                if url.link_username is not None:
                    if does_username_exist(url.link_username):
                        raise HTTPException(status_code=421, detail = "Username already exists")
                    new_id = session.exec(text("SELECT nextval('urldb_id_seq')")).first()
                    hashed_id = does_hash_exist(new_id[0])
                    while hashed_id is None:
                        new_id = session.exec(text("SELECT nextval('urldb_id_seq')")).first()
                        hashed_id = does_hash_exist(new_id[0])
                        
                    user_id_dict = {"id": new_id[0], "shorturl": hashed_id, "user_id": curr_user.id}
                    db_data = UrlDb.model_validate(url, update=user_id_dict)
                    print("DB data :", db_data)
                    session.add(db_data)
                    session.commit()
                    if request.headers.get("hx-request"):
                        return Response(status_code=200, headers={"HX-Redirect": "/dashboard"})
                    return RedirectResponse(url="/dashboard", status_code=200)
                    
                user_id_dict = {"user_id": curr_user.id}
                db_data = UrlDb.model_validate(url, update=user_id_dict)
                session.add(db_data)
                session.commit()
                session.refresh(db_data)
                shortened_url = encode_to_base62(db_data.id)
                url_dict = { "shorturl": shortened_url }
                db_data.sqlmodel_update(url_dict)
                session.add(db_data)
                session.commit()
                session.refresh(db_data)
                return True
            else:
                return False
                return response(status_code=404, detail="Not found")
    except HTTPException:
        raise
    
    except Exception as e:
        logger.exception("An error occurred in create_link:")
        raise HTTPException(status_code=400, detail="Invalid link")
