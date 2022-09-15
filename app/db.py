from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQL_URL = f'postgresql://postgres:postgres@db:5432/postgres'  # адрес базы данных

engine = create_engine(SQL_URL)  # создаётся движок

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)  # задаются сессии

Base = declarative_base()  # задаётся декларативная схема описания данных


# открываем базу данных, совершаем сессию и закрываем в любом случае
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
