from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import RedirectResponse
from sqlmodel import SQLModel, create_engine, select, Field, Session, text
from typing import Annotated

from ..dependencies import get_session, get_current_user
from ..internals.encoders import encode_to_base62, decode_from_base62
from ..models import *
router = APIRouter()

@router.post("/adduser")
def add_users( user: userReq , session: Annotated[Session, Depends(get_session)]):
    user_db = userDb.model_validate(user)
    session.add(user_db)
    session.commit()
    session.refresh(user_db)
    return user_db
    
@router.post("/create", response_model = UrlRes)
def create_link( curr_user: Annotated[currUser, Depends(get_current_user)], url: UrlReq, session: Annotated[Session, Depends(get_session)]):
    full_url = url.fullurl
    if True:
        print("Adding url")
        user_id_dict = {"user_id": curr_user.id}
        db_data = UrlDb.model_validate(url)
        print("Current url data ", db_data)
        session.add(db_data)
        session.commit()
        print("Data commited")
        session.refresh(db_data)
        print("Data refreshed ", db_data)
        shortened_url = encode_to_base62(db_data.id)
        url_dict = { "shorturl": shortened_url }
        db_data.sqlmodel_update(url_dict)
        print("Data updated with url", db_data)
        session.add(db_data)
        session.commit()
        print("New data commited")
        session.refresh(db_data)
        print("Data refreshed ", db_data)
        return UrlRes.model_validate(db_data)
    else:
        raise HTTPException( status_code = 400, detail = "Link not supported or is invalid")
    
@router.get("/url/{shortened_link}", response_class = RedirectResponse)
def redirect_to_full_url( shortened_link: str, session: Annotated[Session, Depends(get_session)]):
    url_id = decode_from_base62(shortened_link)
    if url_id is None:
        raise HTTPException(status_code = 404, detail="not found")
    full_url = session.get(UrlDb, url_id).fullurl
    if full_url is None:
        raise HTTPException(status_code = 404, detail="Link not found")
    print("YOur redirect url is: ", full_url)
    return full_url
    
@router.get("/dashboard")
def user_dashboard( session: Annotated[Session, Depends(get_session)], curr_user: Annotated[currUser, Depends(get_current_user)], offset: Annotated[int | None, Query()] = 0, ):
    url_db = session.exec(select(UrlDb).where(UrlDb.user_id == curr_user.id).offset(0).limit(5)).all()
    url_data = []
    for url in url_db:
        url_data.append(UrlRes.model_validate(url))
    urls_dict = { "urls": url_data }
    print("IN dashboard")
    return userResList.model_validate( curr_user, update = urls_dict)
    
@router.delete("/delete/{url_id}")
def delete_link( url_id: str , session: Annotated[Session, Depends(get_session)], curr_user: Annotated[currUser, Depends(get_current_user)]):
    url_data = session.get(UrlDb, url_id)
    if url_data is None:
        raise HTTPException(status_code = 404, detail="Link not found")
    if usl_data.user_id != curr_user.id:
        raise HTTPException(status_code = 404, detail="Link not found") 
    session.delete(url_data)
    session.commit()
    return { "status_code":200, "Message": "Successfully deleted"}
    
@router.patch("/update")
def update_user(userUpd: userUpdate, curr_user: Annotated[currUser, Depends(get_current_user)], session: Annotated[Session, Depends(get_session)]):
    user_data = session.get(userDb, curr_user.id)
    if user_data is None:
        raise HTTPException(status_code = 404, detail = "User not found")
    updated = userUpd.model_dump(exclude_unset = True)
    user_data.sqlmodel_update(updated)
    session.add(user_data)
    session.commit()
    session.refresh(user_data)
    return userRes.model_validate(user_data)
