from fastapi import APIRouter, Depends, Query, HTTPException, Request, Response
from fastapi.responses import RedirectResponse, HTMLResponse, FileResponse
from sqlmodel import SQLModel, create_engine, select, Field, Session, text, func
from typing import Annotated
from fastapi.templating import Jinja2Templates
from sqlalchemy.schema import Sequence


from ..dependencies import get_session, get_current_user, normalize_url, auth_rate_limit, create_rate_limit, does_username_exist, is_valid_link_username
from ..internals.encoders import encode_to_base62, decode_from_base62
from ..models import *
from ..handlers.create import create_link

from pathlib import Path

MAX_INT32 = 2_147_483_647

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
def create(request:Request,  curr_user: Annotated[currUser, Depends(get_current_user)], url: UrlReqCreate, session: Annotated[Session, Depends(get_session)], is_allowed: Annotated[bool, Depends(create_rate_limit)]):
    if not is_allowed:
        raise HTTPException(status_code = 429, detail = "Too many requests")
    if create_link(request, curr_user, url):
        if request.headers.get("hx-request"):
            return Response(status_code=200, headers={"HX-Redirect": "/dashboard"})
        return RedirectResponse(url="/dashboard", status_code=200)
    return FileResponse("templates/400.html", status_code=400)
    
@router.get("/url/{shortened_link}", response_class = RedirectResponse)
def redirect_to_full_url( shortened_link: str, session: Annotated[Session, Depends(get_session)]):
    url_id = decode_from_base62(shortened_link)
    if url_id > MAX_INT32 or url_id < 1:
        full_url_from_link_username = session.exec(select(UrlDb).where(UrlDb.link_username == shortened_link)).first()
        if full_url_from_link_username is not None:
            print(full_url_from_link_username)
            return full_url_from_link_username.fullurl
        raise HTTPException(status_code=404, detail="Link not found")
    if url_id is None:
        raise HTTPException(status_code=404, detail="Link not found")


    full_url = session.get(UrlDb, url_id)
    full_url_from_username = session.exec(select(UrlDb).where(UrlDb.link_username == shortened_link)).first()
    if full_url is None and full_url_from_link_username is None:
        raise HTTPException(status_code=404, detail="Link not found")

    if full_url is not None and full_url_from_username is None:
        return full_url.fullurl
    if full_url.fullurl is None and full_url_from_link_username is not None:
        return full_url_from_link_username.fullurl
        
@router.get("/u/{shortened_link}", response_class = RedirectResponse)
def redirect_to_full_url( shortened_link: str, session: Annotated[Session, Depends(get_session)]):
    url_id = decode_from_base62(shortened_link)
    if url_id > MAX_INT32 or url_id < 1:
        full_url_from_link_username = session.exec(select(UrlDb).where(UrlDb.link_username == shortened_link)).first()
        if full_url_from_link_username is not None:
            print(full_url_from_link_username)
            return full_url_from_link_username.fullurl
        raise HTTPException(status_code=404, detail="Link not found")
    if url_id is None:
        raise HTTPException(status_code=404, detail="Link not found")


    full_url = session.get(UrlDb, url_id)
    full_url_from_username = session.exec(select(UrlDb).where(UrlDb.link_username == shortened_link)).first()
    if full_url is None and full_url_from_link_username is None:
        raise HTTPException(status_code=404, detail="Link not found")

    if full_url is not None and full_url_from_username is None:
        return full_url.fullurl
    if full_url.fullurl is None and full_url_from_link_username is not None:
        return full_url_from_link_username.fullurl
    
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
    print(url_db[0])
    return templates.TemplateResponse(
    request=request,
    name="dashboard.html",
    context={
        "curr_user": curr_user,
        "urls": url_db,
        "offset": offset,
        "limit": limit,
        "total_count": total_count,
        "current_page": offset // limit + 1,
        "total_pages": max(1, -(-total_count // limit)),
    },
)
    
@router.delete("/delete/{url_id}")
def delete_link( url_id: int , session: Annotated[Session, Depends(get_session)], curr_user: Annotated[currUser, Depends(get_current_user)]):
    url_data = session.get(UrlDb, url_id)
    if url_data is None:
        raise HTTPException(status_code = 404, detail="Link not found")
    if url_data.user_id != curr_user.id:
        raise HTTPException(status_code = 404, detail="Link not found") 
    session.delete(url_data)
    session.commit()
    return RedirectResponse(url="/sdfs", status_code=200)
    
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
    
@router.get("/username/check")
def check_link_username(link_username: str = "", session: Session = Depends(get_session)):
    print(link_username)
    if link_username == "":
        return HTMLResponse(
        content='<span style="color: #22c55e;"></span>',
        headers={"HX-Trigger": "usernameAvailable"},
    )
    if not is_valid_link_username(link_username):
        return HTMLResponse(
            content='<span style="color: #ef4444;">username should only be alphanumeric and not longer then 15 chars</span>',
            headers={"HX-Trigger": "usernameTaken"},
        )
    if does_username_exist(link_username):
        return HTMLResponse(
            content='<span style="color: #ef4444;">username already taken</span>',
            headers={"HX-Trigger": "usernameTaken"},
        )
    
    return HTMLResponse(
        content='<span style="color: #22c55e;">username available!</span>',
        headers={"HX-Trigger": "usernameAvailable"},
    )
    
