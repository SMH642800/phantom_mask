import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.models import Base
from app.api import pharmacies, users, purchase, summary, search


# Define a test-specific SQLite DB
TEST_DB_URL = "sqlite:///test_db.sqlite"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Recreate database schema before tests
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

# Override FastAPI dependency for all routers
@pytest.fixture(scope="module")
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides = {}
    app.dependency_overrides[pharmacies.get_db] = override_get_db
    app.dependency_overrides[users.get_db] = override_get_db
    app.dependency_overrides[purchase.get_db] = override_get_db
    app.dependency_overrides[summary.get_db] = override_get_db
    app.dependency_overrides[search.get_db] = override_get_db

    yield TestClient(app)
