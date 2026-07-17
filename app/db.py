from sqlmodel import create_engine

sql_name = "database.db"
sql_url = f"sqlite:///{sql_name}"

engine = create_engine(sql_url, echo=True)
