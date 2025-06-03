import os
import sys
import pytest
import pytest_asyncio
from httpx import AsyncClient
from httpx._transports.asgi import ASGITransport
from dotenv import load_dotenv

# Add the project root directory to PYTHONPATH
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from app.main import app
from app.database import database
from app.models import users, tasks1  # Assuming tasks1 is the table name for user tasks

# Load environment variables
load_dotenv()


@pytest_asyncio.fixture
async def setup_database():
    await database.connect()
    yield
    await database.disconnect()


@pytest_asyncio.fixture
async def test_client(setup_database):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def create_test_user(test_client):
    payload = {
        "first_name": "Test1",
        "last_name": "User1",
        "username": "testloginuser1",
        "password": "1234567891"
    }
    # Register user through the signup endpoint
    await test_client.post("/signup", json=payload)
    
    yield

    # Cleanup: get user id, delete tasks first, then user
    user_query = users.select().where(users.c.username == "testloginuser1")
    user = await database.fetch_one(user_query)
    if user:
        await database.execute(tasks1.delete().where(tasks1.c.user_id == user.id))
        await database.execute(users.delete().where(users.c.id == user.id))


@pytest.mark.asyncio
async def test_login_success(test_client, create_test_user):
    payload = {
        "username": "testloginuser1",
        "password": "1234567891"
    }
    response = await test_client.post("/login", json=payload)
    assert response.status_code == 200
    json_data = response.json()
    assert "access_token" in json_data
    assert json_data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_password(test_client, create_test_user):
    payload = {
        "username": "testloginuser1",
        "password": "wrongpassword"
    }
    response = await test_client.post("/login", json=payload)
    assert response.status_code in [400, 401]
    assert response.json()["detail"] == "Invalid username or password"


@pytest.mark.asyncio
async def test_login_nonexistent_user(test_client):
    payload = {
        "username": "nonexistentuser",
        "password": "irrelevant"
    }
    response = await test_client.post("/login", json=payload)
    assert response.status_code in [400, 401]
    assert response.json()["detail"] == "Invalid username or password"


@pytest.mark.asyncio
async def test_login_missing_fields(test_client):
    payload = {
        "username": "useronly"
        # Missing password
    }
    response = await test_client.post("/login", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_empty_fields(test_client):
    payload = {
        "username": "",
        "password": ""
    }
    response = await test_client.post("/login", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid username or password"
