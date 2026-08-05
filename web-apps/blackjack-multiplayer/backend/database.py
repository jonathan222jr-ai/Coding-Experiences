from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# create instance folder if not exists
os.makedirs("instance", exist_ok=True)

DATABASE_URL = "sqlite:///instance/database.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()
