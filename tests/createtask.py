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
from app.models import users, tasks1

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
async def get_token(test_client):
    # Create test user
    signup_payload = {
        "first_name": "John224",
        "last_name": "Doe",
        "username": "johndoe224",
        "password": "securepassword"
    }
    signup_response = await test_client.post("/signup", json=signup_payload)
    print("Signup Response:", signup_response.status_code, signup_response.json())  # Debugging

    login_payload = {
        "username": "johndoe224",
        "password": "securepassword"
    }
    login_response = await test_client.post("/login", json=login_payload)
    print("Login Response:", login_response.status_code, login_response.json())  # Debugging

    # Retrieve the token
    token = login_response.json().get("access_token")
    print("Retrieved Token:", token)  # Debugging
    if not token:
        raise ValueError("Failed to retrieve access token")

    yield token


# ✅ Positive Test Case

@pytest.mark.asyncio
async def test_create_task_valid(test_client, get_token):
    payload = {
        "title": "Task for Sam123",  # Required field
        "description": "Project on Fast API",  # Optional field
        "due_date": "2025-09-06"  # Optional field
    }
    headers = {"Authorization": get_token}
    response = await test_client.post("/tasks/", json=payload, headers=headers)
    print("Response Status Code:", response.status_code)
    print("Response JSON:", response.json())  # Debugging

    # Assert the response status code
    assert response.status_code == 201  # Expecting success

    # Assert the response JSON
    data = response.json()
    assert data.get("id") is not None  # Ensure the task ID is generated
    assert data.get("title") == payload["title"]
    assert data.get("description") == payload["description"]
    assert data.get("due_date") == payload["due_date"]
    assert data.get("status") == "active"
    assert data.get("time_of_generation") is not None  # Ensure the timestamp is generated
    assert data.get("user_id") is not None  # Ensure the user ID is included


# ❌ Missing Fields

@pytest.mark.asyncio
async def test_create_task_missing_title(test_client, get_token):
    payload = {
        "description": "No title provided",
        "due_date": "2025-12-31T23:59:59"
    }
    headers = {"Authorization": get_token}
    response = await test_client.post("/tasks/", json=payload, headers=headers)
    print("Response Status Code:", response.status_code)
    print("Response JSON:", response.json())  # Debugging

    assert response.status_code == 400  # Validation error


@pytest.mark.asyncio
async def test_create_task_missing_description(test_client, get_token):
    payload = {
        "title": "Task without description",
        "due_date": "2025-12-31T23:59:59"
    }
    headers = {"Authorization": get_token}
    response = await test_client.post("/tasks/", json=payload, headers=headers)
    print("Response Status Code:", response.status_code)
    print("Response JSON:", response.json())  # Debugging

    assert response.status_code == 400  # Description is optional


# ❌ Invalid Input

@pytest.mark.asyncio
async def test_create_task_invalid_date(test_client, get_token):
    payload = {
        "title": "Invalid Date",
        "description": "Bad date format",
        "due_date": "31-12-2025"  # Invalid ISO 8601 format
    }
    headers = {"Authorization": f"Bearer {get_token}"}
    response = await test_client.post("/tasks/", json=payload, headers=headers)
    print("Response Status Code:", response.status_code)
    print("Response JSON:", response.json())  # Debugging

    assert response.status_code == 401  # Validation error


@pytest.mark.asyncio
async def test_create_task_empty_fields(test_client, get_token):
    payload = {
        "title": "",
        "description": "",
        "due_date": "2025-12-31T23:59:59"
    }
    headers = {"Authorization": f"Bearer {get_token}"}
    response = await test_client.post("/tasks/", json=payload, headers=headers)
    print("Response Status Code:", response.status_code)
    print("Response JSON:", response.json())  # Debugging

    assert response.status_code in [400, 422, 401]  # Validation error


@pytest.mark.asyncio
async def test_create_task_very_long_title(test_client, get_token):
    payload = {
        "title": "A" * 1000,  # Overly long title
        "description": "Valid description",
        "due_date": "2025-12-31T23:59:59"
    }
    headers = {"Authorization": f"Bearer {get_token}"}
    response = await test_client.post("/tasks/", json=payload, headers=headers)
    print("Response Status Code:", response.status_code)
    print("Response JSON:", response.json())  # Debugging

    assert response.status_code in [201, 422, 401]  # Allow if no max_length, else 422


# ❌ Unauthorized Access

@pytest.mark.asyncio
async def test_create_task_unauthorized(test_client):
    payload = {
        "title": "Unauthorized",
        "description": "No token provided",
        "due_date": "2025-12-31T23:59:59"
    }
    response = await test_client.post("/tasks/", json=payload)
    print("Response Status Code:", response.status_code)
    print("Response JSON:", response.json())  # Debugging

    assert response.status_code == 401
