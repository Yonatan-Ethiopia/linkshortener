from fastapi import APIRouter, Depends, Query, HTTPException, Request, Response
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlmodel import SQLModel, create_engine, select, Field, Session, text, func
from typing import Annotated
from fastapi.templating import Jinja2Templates


from ..dependencies import get_session, get_current_user, normalize_url, auth_rate_limit, create_rate_limit
from ..internals.encoders import encode_to_base62, decode_from_base62
from ..models import *

from pathlib import Path

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

@router.post("/adduser")
def add_users( user: userReq , session: Annotated[Session, Depends(get_session)]):
    user_db = userDb.model_validate(user)
    session.add(user_db)
    session.commit()
    session.refresh(user_db)
    return user_db
    
@router.post("/create", response_model = UrlRes)
def create_link(request:Request,  curr_user: Annotated[currUser, Depends(get_current_user)], url: UrlReqCreate, session: Annotated[Session, Depends(get_session)], is_allowed: Annotated[bool, Depends(create_rate_limit)]):
    if not is_allowed:
        raise HTTPException(status_code = 429, detail = "Too many requests")
    full_url = url.fullurl
    full_url = normalize_url(full_url)
    if full_url is not None:
        url.fullurl = full_url
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
        if request.headers.get("hx-request"):
            return Response(status_code=200, headers={"HX-Redirect": "/dashboard"})
        return UrlRes.model_validate(db_data)
    else:
        raise HTTPException( status_code = 400, detail = "Link not supported or is invalid")
    
@router.get("/url/{shortened_link}", response_class = RedirectResponse)
def redirect_to_full_url( shortened_link: str, session: Annotated[Session, Depends(get_session)]):
    url_id = decode_from_base62(shortened_link)
    if url_id is None:
        raise HTTPException(status_code = 404, detail="not found")

    full_url = session.get(UrlDb, url_id)
    if full_url is None:
        raise HTTPException(status_code = 404, detail="Link not found")

    print("Your redirect url is: ", full_url.fullurl)
    return full_url.fullurl
    
@router.get("/dashboard", response_class=HTMLResponse)
def user_dashboard( request: Request, session: Annotated[Session, Depends(get_session)], curr_user: Annotated[currUser, Depends(get_current_user)], offset: Annotated[int | None, Query()] = 0, ):
    limit = 5
    url_db = session.exec(select(UrlDb).where(UrlDb.user_id == curr_user.id).order_by(UrlDb.id.desc()).offset(offset).limit(5)).all()
    total_count = session.exec(
        select(func.count()).select_from(UrlDb).where(UrlDb.user_id == curr_user.id)
    ).one()
    url_data = []
    for url in url_db:
        url_data.append(UrlRes.model_validate(url))
    urls_dict = { "urls": url_data }
    print("IN dashboard")
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "curr_user": curr_user,
        "urls": url_db,
        "offset": offset,
        "limit": limit,
        "total_count": total_count,
        "current_page": offset // limit + 1,
        "total_pages": max(1, -(-total_count // limit)),
    })
    
@router.delete("/delete/{url_id}")
def delete_link( url_id: int , session: Annotated[Session, Depends(get_session)], curr_user: Annotated[currUser, Depends(get_current_user)]):
    url_data = session.get(UrlDb, url_id)
    if url_data is None:
        raise HTTPException(status_code = 404, detail="Link not found")
    if url_data.user_id != curr_user.id:
        raise HTTPException(status_code = 404, detail="Link not found") 
    session.delete(url_data)
    session.commit()
    return Response(status_code=200)
    
@router.patch("/update")
def update_user(response: Response, userUpd: userUpdate, curr_user: Annotated[currUser, Depends(get_current_user)], session: Annotated[Session, Depends(get_session)]):
    user_data = session.get(userDb, curr_user.id)
    if user_data is None:
        raise HTTPException(status_code = 404, detail = "User not found")
    updated = userUpd.model_dump(exclude_unset = True)
    user_data.sqlmodel_update(updated)
    session.add(user_data)
    session.commit()
    session.refresh(user_data)
    response.headers["HX-Refresh"] = "true"
    return ""
