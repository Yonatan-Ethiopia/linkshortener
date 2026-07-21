from sqlmodel import SQLModel, Field
from datetime import datetime, timezone

class UrlBase(SQLModel):
    fullurl: str
    
class UrlDb(UrlBase, table = True):
    id: int | None = Field( default = None, primary_key=True , sa_column_kwargs={"autoincrement": True},)
    shorturl: str | None = Field( default = None, index=True)
    user_id: int = Field( foreign_key = "userdb.id", index = True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
class UrlReq(UrlBase):
    user_id: int
    
class UrlReqCreate(UrlBase):
    pass
    
class UrlRes(UrlBase):
    shorturl : str | None
    id: int
    created_at: datetime | None
    
class userBase(SQLModel):
    name: str
    email: str
class currUser(userBase):
    pass
    
class userDb(userBase, table = True):
    id: int | None = Field( default = None, primary_key = True )
    google_sub: str = Field( unique = True, index = True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class userRes(userBase):
    pass    
class userResList(userRes):
    urls: list[UrlRes]
    
class userReq(userBase):
    pass
    
class userUpdate(SQLModel):
    name : str | None = None
    email: str | None = None
