from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

TEST_DB_PATH = Path("./data/test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{Path('./data/test.db')}"
os.environ["ENABLE_POLLER"] = "false"

from app.api.deps import get_db
from app.db.base import Base
from app.main import app

@pytest.fixture(scope="session")
def test_db_file():
    TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not TEST_DB_PATH.exists():
        TEST_DB_PATH.touch()

    yield TEST_DB_PATH


@pytest.fixture()
def db_session(test_db_file) -> Session:
    os.environ["DATABASE_URL"] = f"sqlite:///{test_db_file}"
    engine = create_engine(os.environ["DATABASE_URL"], connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session: Session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
