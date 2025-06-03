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
from app.models import users  # Import the users table model


# Load environment variables from .env file
load_dotenv()

@pytest_asyncio.fixture
async def setup_database():
    # Connect to the database before each test
    await database.connect()
    yield
    # Disconnect from the database after each test
    await database.disconnect()

@pytest_asyncio.fixture
async def test_client(setup_database):
    # Use ASGITransport to test the FastAPI app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

@pytest_asyncio.fixture
async def cleanup_users():
    # Cleanup logic to remove test users after each test
    yield
    query = users.delete()  # Delete all records from the users table
    await database.execute(query)

@pytest.mark.asyncio
async def test_signup_success(test_client):
    payload = {
        "first_name": "John2",
        "last_name": "Miller2",
        "username": "johnmiller2",
        "password": "1234567891"
    }
    response = await test_client.post("/signup", json=payload)
    print("Response:", response.json())  # Debugging line to see the response
    assert response.status_code == 201
    assert response.json() == {"message": "User created successfully"}

@pytest.mark.asyncio
async def test_signup_existing_user(test_client):
    payload = {
        "first_name": "John2",
        "last_name": "Miller2",
        "username": "johnmiller2",
        "password": "1234567891"
    }
    response = await test_client.post("/signup", json=payload)
    assert response.status_code == 400
    assert response.json() == {"detail": "Username already registered"}
    
@pytest.mark.asyncio
async def test_signup_missing_username(test_client):
    payload = {
        "first_name": "Alice",
        "last_name": "Brown",
        "password": "password123"
    }
    response = await test_client.post("/signup", json=payload)
    assert response.status_code == 422  # Unprocessable Entity
    assert "username" in response.text
    
@pytest.mark.asyncio
async def test_signup_empty_fields(test_client):
    payload = {
        "first_name": "",
        "last_name": "",
        "username": "",
        "password": ""
    }
    response = await test_client.post("/signup", json=payload)
    assert response.status_code == 422


