from fastapi import FastAPI, HTTPException, Depends, status, Header
from fastapi.security import OAuth2PasswordRequestForm
from app.models import users, tasks1
from app.schemas import UserSignup, UserLogin, TaskCreate, TaskUpdate, TaskOut
from app.database import database, metadata, engine
from app.auth import get_password_hash, verify_password, create_access_token, decode_access_token
from sqlalchemy import select, and_, or_
from typing import List, Optional
from datetime import datetime



app = FastAPI()

# Create tables if not exists (optional)
metadata.create_all(engine)

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Task Management API"}

# Signup API
@app.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(user: UserSignup):
    query = users.select().where(users.c.username == user.username)
    existing_user = await database.fetch_one(query)
    if (existing_user):
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_password = get_password_hash(user.password)
    query = users.insert().values(
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
        password=hashed_password
    )
    await database.execute(query)
    return {"message": "User created successfully"}

# Login API
@app.post("/login")
async def login(user: UserLogin):
    query = users.select().where(users.c.username == user.username)
    db_user = await database.fetch_one(query)
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=400, detail="Invalid username or password")

    token = create_access_token({"sub": db_user["username"]})
    # Store token in tasks table with dummy task (or you can create a separate token table if preferred)
    # But as per your requirement, token is stored in tasks table linked with user
    # So here we create a task with token on login (a bit unusual but per requirement)
    query = tasks1.insert().values(
        title="Login Token",
        description="JWT token generated on login",
        token=token,
        time_of_generation=datetime.utcnow(),
        status="active",
        user_id=db_user["id"],
        due_date=None
    )
    await database.execute(query)

    return {"access_token": token, "token_type": "bearer"}

# Dependency to get current user from token
async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    username = decode_access_token(authorization)
    if username is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    query = users.select().where(users.c.username == username)
    user = await database.fetch_one(query)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# Create Task
@app.post("/tasks/", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate, current_user=Depends(get_current_user)):
    query = tasks1.insert().values(
        title=task.title,
        
        description=task.description,
        
        time_of_generation=datetime.utcnow(),
        status="active",
        user_id=current_user.id,
        due_date=task.due_date
    )
    task_id = await database.execute(query)
    return {
        "id": task_id,
        "title": task.title,
        "description": task.description,
        "status": "active",
        "time_of_generation": datetime.utcnow(),
        "user_id": current_user.id,
        "due_date": task.due_date
    }
# Get all tasks of current user

@app.get("/tasks/", response_model=List[TaskOut])
async def get_tasks(search_keyword: Optional[str] = None, current_user=Depends(get_current_user)):
    # Base query to fetch tasks for the current user
    query = tasks1.select().where(tasks1.c.user_id == current_user["id"])

    # If search_keyword is provided, filter tasks by title, description, or ID
    if search_keyword:
        query = query.where(
            or_(
                tasks1.c.id == search_keyword if search_keyword.isdigit() else None,
                tasks1.c.title.ilike(f"%{search_keyword}%"),
                tasks1.c.description.ilike(f"%{search_keyword}%")
            )
        )

    # Order tasks by ID in ascending order
    query = query.order_by(tasks1.c.id.asc())

    # Execute the query and fetch all matching tasks
    tasks = await database.fetch_all(query)

    # If no tasks are found, return an empty list
    return tasks

# Get task by id
@app.get("/tasks/{task_id}", response_model=TaskOut)
async def get_task(task_id: int, current_user=Depends(get_current_user)):
    query = tasks1.select().where(
        and_(
            tasks1.c.id == task_id,
            tasks1.c.user_id == current_user["id"]
        )
    )
    task = await database.fetch_one(query)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

# Update task
@app.put("/tasks/{task_id}", response_model=TaskOut)
async def update_task(task_id: int, task: TaskUpdate, current_user=Depends(get_current_user)):
    query = tasks1.select().where(
        and_(
            tasks1.c.id == task_id,
            tasks1.c.user_id == current_user["id"]
        )
    )
    existing_task = await database.fetch_one(query)
    if not existing_task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = task.dict(exclude_unset=True)
    if update_data:
        update_query = tasks1.update().where(tasks1.c.id == task_id).values(**update_data)
        await database.execute(update_query)

    query = tasks1.select().where(tasks1.c.id == task_id)
    updated_task = await database.fetch_one(query)
    return updated_task

# Delete task
@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int, current_user=Depends(get_current_user)):
    query = tasks1.select().where(
        and_(
            tasks1.c.id == task_id,
            tasks1.c.user_id == current_user["id"]
        )
    )
    task = await database.fetch_one(query)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    delete_query = tasks1.delete().where(tasks1.c.id == task_id)
    await database.execute(delete_query)
    return {"detail": "Task deleted"}
