import logging
import os
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects import postgresql
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger("uvicorn")
database_url = os.environ.get("DATABASE_URL")
print(database_url)
engine = create_engine(database_url, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
