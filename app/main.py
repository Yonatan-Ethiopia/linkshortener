from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.responses import RedirectResponse
from sqlmodel import SQLModel, create_engine, select, Field, Session, text
from typing import Annotated
import string

class UrlBase(SQLModel):
    fullurl: str
    
class UrlDb(UrlBase, table = True):
    id: int | None = Field( default = None, primary_key=True , sa_column_kwargs={"autoincrement": True},)
    shorturl: str | None = Field( default = None, index=True)
    user_id: int = Field( foreign_key = "userdb.id", index = True)
    
class UrlReq(UrlBase):
    user_id: int
    
class UrlRes(UrlBase):
    shorturl : str | None
    id: int
    
class userBase(SQLModel):
    name: str
    email: str
class currUser(userBase):
    pass
    
class userDb(userBase, table = True):
    id: int | None = Field( default = None, primary_key = True )

class userRes(userBase):
    pass    
class userResList(userRes):
    urls: list[UrlRes]
    
class userReq(userBase):
    pass
    
class userUpdate(SQLModel):
    name : str | None = None
    email: str | None = None
    username: str | None = None
    

def encode_to_base62( number: int):
    chars = string.digits + string.ascii_letters
    if number == 0:
        return chars[0]
    base62 = []
    while number > 0:
        print("This is running still")
        number, rem = divmod(number, 62)
        base62.append(chars[rem])
    print("Finished")
    return "".join(reversed(base62))
    
def decode_from_base62( short_string: str):
    chars = string.digits + string.ascii_letters
    char_map = {char: i for i, char in enumerate(chars)}
    num = 0
    for char in short_string:
        num = num * 62 + char_map[char]
    return num
    
sql_name = "database.db"
sql_url = f"sqlite:///{sql_name}"

engine = create_engine(sql_url, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

app = FastAPI()

def get_session():
    with Session(engine) as session:
        yield session
        
def get_current_user( session: Annotated[Session, Depends(get_session)]):
    user = session.exec(select(userDb)).first()
    print("The user is ", user)
    return user
    
        
@app.on_event("startup")
def initdb():
    create_db_and_tables()
    
@app.post("/adduser")
def add_users( user: userReq , session: Annotated[Session, Depends(get_session)]):
    user_db = userDb.model_validate(user)
    session.add(user_db)
    session.commit()
    session.refresh(user_db)
    return user_db
    
@app.post("/create", response_model = UrlRes)
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
    
@app.get("/url/{shortened_link}", response_class = RedirectResponse)
def redirect_to_full_url( shortened_link: str, session: Annotated[Session, Depends(get_session)]):
    url_id = decode_from_base62(shortened_link)
    if url_id is None:
        raise HTTPException(status_code = 404, detail="not found")
    full_url = session.get(UrlDb, url_id).fullurl
    if full_url is None:
        raise HTTPException(status_code = 404, detail="Link not found")
    print("YOur redirect url is: ", full_url)
    return full_url
    
@app.get("/dashboard")
def user_dashboard( session: Annotated[Session, Depends(get_session)], curr_user: Annotated[currUser, Depends(get_current_user)], offset: Annotated[int | None, Query()] = 0, ):
    url_db = session.exec(select(UrlDb).where(UrlDb.user_id == curr_user.id).offset(0).limit(5)).all()
    url_data = []
    for url in url_db:
        url_data.append(UrlRes.model_validate(url))
    urls_dict = { "urls": url_data }
    print("IN dashboard")
    return userResList.model_validate( curr_user, update = urls_dict)
    
@app.get("/delete/{url_id}")
def delete_link( url_id: str , session: Annotated[Session, Depends(get_session)]):
    url_data = session.get(UrlDb, url_id)
    if url_data is None:
        raise HTTPException(status_code = 404, detail="Link not found")
    session.delete(url_data)
    session.commit()
    return { "status_code":200, "Message": "Successfully deleted"}
    
@app.patch("/update")
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
    
    
    

    
    
