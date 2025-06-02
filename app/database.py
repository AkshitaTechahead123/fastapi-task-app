from sqlalchemy import create_engine, MetaData
from databases import Database
from sqlalchemy.orm import sessionmaker, declarative_base

# PostgreSQL credentials — replace with your own
DB_USER = "postgres"
DB_PASSWORD = "12345"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "postgres"

# Construct the database URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create the database object (async)
database = Database(DATABASE_URL)

# Create SQLAlchemy engine (sync, for table creation)
engine = create_engine(DATABASE_URL, echo=True)

# Metadata for table definitions
metadata = MetaData()

# Base for ORM (optional, not used in your current models)
Base = declarative_base()

# Session (for synchronous DB operations if needed)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Optional helper to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        

engine = create_engine(
    DATABASE_URL,
    echo=False  # Turn off SQL statements in console
)
