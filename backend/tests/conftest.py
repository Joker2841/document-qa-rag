import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def test_db():
    # Create the database and tables
    Base.metadata.create_all(bind=engine)
    
    # Create test files directory if it doesn't exist
    os.makedirs("test_files", exist_ok=True)
    
    yield  # Run the tests
    
    # Drop the tables after testing
    Base.metadata.drop_all(bind=engine)
    
    # Remove test files
    # import shutil
    # shutil.rmtree("test_files", ignore_errors=True)


@pytest.fixture(scope="function")
def db_session(test_db):
    """Creates a fresh database session for each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client using the test database."""
    def _get_test_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides = {}