from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User
from passlib.hash import bcrypt
from pydantic import BaseModel, Field, constr

# Constants
MAX_PASSWORD_LENGTH = 72

# --- Pydantic models ---
class SignupRequest(BaseModel):
    username: constr(strip_whitespace=True, min_length=3, max_length=50)
    password: constr(min_length=6, max_length=MAX_PASSWORD_LENGTH)

class LoginRequest(BaseModel):
    username: str
    password: str

# --- Router ---
router = APIRouter()

# --- DB session dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Signup endpoint ---
@router.post("/signup")
def signup(data: SignupRequest, db: Session = Depends(get_db)):
    # Check if user exists
    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    # Hash password (truncate if necessary)
    password_to_hash = data.password[:MAX_PASSWORD_LENGTH]
    user = User(username=data.username, password_hash=bcrypt.hash(password_to_hash))

    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "Account created", "user_id": user.id}

# --- Login endpoint ---
@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # Truncate password before verifying
    if not bcrypt.verify(data.password[:MAX_PASSWORD_LENGTH], user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    return {"message": "Logged in", "user_id": user.id}
