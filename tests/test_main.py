import os
import random

import pytest
# from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.testclient import TestClient

from app.db import Base
from app.main import app

# load_dotenv()


def get_test_db_url():
    """Returns the test database URL."""
    return os.environ.get("DATABASE_TEST_URL")


os.environ["DATABASE_URL"] = get_test_db_url()

database_test_url = os.environ.get("DATABASE_TEST_URL")
engine = create_engine(database_test_url)


def override_get_db():
    """Override get_db to use the test database."""
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = session_local()
    Base.metadata.create_all(bind=engine)

    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def random_number():
    """Fixture to generate a random number for testing purposes."""
    return random.randint(1, 1000)


@pytest.fixture(scope="session")
def test_app():
    """Fixture to create a TestClient for testing the FastAPI app."""
    os.environ["DATABASE_URL"] = get_test_db_url()

    from app.db import Base, get_db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client
        Base.metadata.drop_all(bind=engine)
