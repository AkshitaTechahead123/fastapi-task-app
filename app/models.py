from sqlalchemy import Table, Column, Integer, String, Text, ForeignKey, TIMESTAMP, Date, VARCHAR
from sqlalchemy.sql import func
from app.database import metadata

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("first_name", VARCHAR(100), nullable=False),
    Column("last_name", VARCHAR(100), nullable=False),
    Column("username", VARCHAR(100), unique=True, nullable=False),
    Column("password", Text, nullable=False),
)

tasks = Table(
    "tasks",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("title", Text, nullable=False),
    Column("description", Text),
    Column("token", Text, nullable=False),
    Column("time_of_generation", TIMESTAMP(timezone=True), server_default=func.now()),
    Column("status", VARCHAR(20), default="active"),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE")),
    Column("due_date", Date, nullable=True),
)
