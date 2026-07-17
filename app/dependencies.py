from sqlmodel import SQLModel, session, select

def get_session():
    with Session(engine) as session:
        yield session
        
def get_current_user( session: Annotated[Session, Depends(get_session)]):
    user = session.exec(select(userDb)).first()
    print("The user is ", user)
    return user
    
