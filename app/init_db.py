
from app.models import Base
from app.db import engine

# Script to initialize the database schema (create all tables)
if __name__ == '__main__':
    Base.metadata.create_all(bind=engine)
    print("✅ Database created successfully.")
