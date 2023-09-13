import logging
import os
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

log = logging.getLogger("uvicorn")
"""""
SessionLocal = None
Base = None
engine = None


def init_db(app: FastAPI):
    database_url = os.environ.get("DATABASE_URL_TEST")
    print(database_url)
    engine = create_engine(database_url)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base = declarative_base()
"""

