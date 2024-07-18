import pytest
from httpx import AsyncClient
import main
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
from routers.users import get_db
from models import Users, Chat_History
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from jose import jwt


SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

main.app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def client():
    with TestClient(main.app) as c:
        yield c

@pytest.fixture
def user_token():
    def create_access_token(username: str, user_id: int, role: str, expires_delta: timedelta):
        SECRET_KEY = '197b2c37c391bed93fe80344fe73b806947a65e36206e05a1a23c2fa12702fe3'
        ALGORITHM = 'HS256'
        encode = {'sub': username, 'id': user_id, 'role': role}
        expire = datetime.utcnow() + expires_delta
        encode.update({'exp': expire})
        return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

    return create_access_token("testuser", 1, "user", timedelta(minutes=30))

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    test_user = Users(
        id=1,
        email="test@example.com",
        username="testuser",
        first_name="Test",
        last_name="User",
        hashed_password="$2b$12$KIXcQbJ1O9aClwFkn7C8GuRkGZn8z3O/lcHeW68f7MxHGJY04Hh6S",  # "password"
        role="user"
    )
    db.add(test_user)
    db.commit()
    db.close()

@pytest.mark.asyncio
async def test_get_users(client, user_token):
    headers = {"Authorization": f"Bearer {user_token}"}
    async with AsyncClient(app=main.app, base_url="http://test") as ac:
        response = await ac.get("/users/", headers=headers)
    assert response.status_code == 200
    assert response.json()['username'] == 'testuser'

@pytest.mark.asyncio
async def test_get_user_chat_history(client, user_token):
    db = TestingSessionLocal()
    chat_history = Chat_History(user_id=1, message="Hello", response="Hi", timestamp=datetime.utcnow())
    db.add(chat_history)
    db.commit()

    # Debugging: Print the chat history from the database
    all_chat_history = db.query(Chat_History).all()
    print(f"All Chat History in DB: {[{'username': ch.user_id, 'message': ch.message, 'response': ch.response, 'timestamp': ch.timestamp} for ch in all_chat_history]}")

    added_history = db.query(Chat_History).filter(Chat_History.user_id == 1).first()
    assert added_history is not None, "Chat_History entry was not added to the database."

    db.close()

    headers = {"Authorization": f"Bearer {user_token}"}
    async with AsyncClient(app=main.app, base_url="http://test") as ac:
        response = await ac.get("/chat/chat_history", headers=headers)

    print(f"Response JSON: {response.json()}")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0, "The response list is empty."
    assert response.json()[0]["message"] == "Hello"
    assert response.json()[0]["response"] == "Hi"
