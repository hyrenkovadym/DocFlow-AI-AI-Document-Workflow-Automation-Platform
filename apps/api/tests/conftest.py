import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User


@pytest.fixture()
def db_session(tmp_path: Path) -> Session:
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite+pysqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session: Session, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    os.environ["AI_PROVIDER"] = "mock"
    os.environ["UPLOAD_DIR"] = str(tmp_path / "uploads")

    from app.core.config import get_settings

    get_settings.cache_clear()

    from app.main import app
    from app.services import document_service

    class _DummyTask:
        @staticmethod
        def delay(_document_id: str) -> None:
            return None

    monkeypatch.setattr(document_service, "process_document_task", _DummyTask)

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture()
def create_user(db_session: Session):
    from app.core.security import get_password_hash

    def _create_user(
        *, email: str, password: str, role: UserRole = UserRole.USER, full_name: str = "Test User"
    ) -> User:
        user = User(
            email=email,
            full_name=full_name,
            role=role,
            hashed_password=get_password_hash(password),
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return _create_user


def login(client: TestClient, email: str, password: str) -> str:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]
