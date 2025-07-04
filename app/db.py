import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Database connection URL (default: SQLite file db.sqlite)
DATABASE_URL = "sqlite:///db.sqlite"

# SQLAlchemy engine and session factory
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)