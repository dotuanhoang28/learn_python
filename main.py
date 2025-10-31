from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
import uvicorn
import datetime
import os
import json
import re
from sqlalchemy import Column, Integer, String, create_engine, select
from sqlalchemy.orm import declarative_base, sessionmaker
USER_FILE = os.path.join(os.path.dirname(__file__), "users.txt")

app = FastAPI(title="Basic User CRUD API")


class User(BaseModel):
    name: str
    age: int
    dob: str
    address: str
    phone_number: str
    email: str
    username: str
    password: str = Field(..., exclude=True)


# In-memory store as indexable list by numeric ID. Use None for deleted slots to keep IDs stable.
def load_users_from_file():
    users = []
    if not os.path.exists(USER_FILE):
        return users
    try:
        with open(USER_FILE, "r", encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line.strip())
                users.append(rec)
    except Exception:
        pass  # empty/corrupt file
    return users

user_store: List[Optional[Dict[str, Any]]] = load_users_from_file()

# === SQLAlchemy setup (SQLite) ===
DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"
Base = declarative_base()

class UserModel(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    dob = Column(String, nullable=False)
    address = Column(String, nullable=False)
    phone_number = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base.metadata.create_all(engine)

# INSERT_YOUR_CODE



def is_email_valid(email: str) -> bool:
    # More specific validation using a regular expression for standard email formats
    if not isinstance(email, str):
        return False
    email_regex = re.compile(
        r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:\.[a-zA-Z]{2,})*$"
    )
    return re.match(email_regex, email) is not None



def is_phone_number_valid(phone_number: str) -> bool:
    return phone_number.isdigit()

def is_age_valid(age: int) -> bool:
    try:
        age_int = int(age)
        return 0 < age_int < 100
    except ValueError:
        return False

def is_dob_valid(dob: str) -> bool:
    try:
        dob_date = datetime.date.fromisoformat(dob)
        today = datetime.date.today()
        age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
        # Age must be > 0 and < 100 years
        return 0 < age < 100
    except ValueError:
        return False
        
def save_users_to_file():
    # Only save non-None users
    with open(USER_FILE, "w", encoding="utf-8") as f:
        for user in user_store:
            if user is not None:
                # Save all fields
                f.write(json.dumps(user) + "\n")


# ===== JSON API: CRUD =====

@app.post("/users", response_model=User, status_code=201)
async def create_user(user: User):
    # Enforce unique username
    for user_data in user_store:
        if user_data is not None and user_data.get("username") == user.username:
            raise HTTPException(status_code=409, detail="Username already exists")
        if user_data is not None and user_data.get("phone_number") == user.phone_number:
            raise HTTPException(status_code=409, detail="Phone number already exists")
    if not is_phone_number_valid(user.phone_number):
        raise HTTPException(status_code=422, detail="Invalid phone number. Digits only.")
    if not is_age_valid(user.age):
        raise HTTPException(status_code=422, detail="Invalid age. Must be 1-99.")
    if not is_dob_valid(user.dob):
        raise HTTPException(status_code=422, detail="Invalid date.")
    if not is_email_valid(user.email):
        raise HTTPException(status_code=422, detail="Invalid email format.")

    # Save to DB
    with SessionLocal() as db:
        db_user = UserModel(
            name=user.name,
            age=user.age,
            dob=user.dob,
            address=user.address,
            phone_number=user.phone_number,
            email=user.email,
            username=user.username,
            password=user.password,
        )
        db.add(db_user)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise HTTPException(status_code=409, detail="Username or phone already exists")
        db.refresh(db_user)

    # Mirror to file (refresh from DB for simplicity)
    with SessionLocal() as db:
        rows = db.execute(select(UserModel)).scalars().all()
        global user_store
        user_store = [
            {
                "name": r.name,
                "age": r.age,
                "dob": r.dob,
                "address": r.address,
                "phone_number": r.phone_number,
                "email": r.email,
                "username": r.username,
                "password": r.password,
            }
            for r in rows
        ]
    save_users_to_file()
    return User(**{
        "name": user.name,
        "age": user.age,
        "dob": user.dob,
        "address": user.address,
        "phone_number": user.phone_number,
        "email": user.email,
        "username": user.username,
        "password": user.password,
    })
    

@app.get("/users", response_model=List[User])
async def list_users():
    with SessionLocal() as db:
        rows = db.execute(select(UserModel)).scalars().all()
        return [
            User(
                name=r.name,
                age=r.age,
                dob=r.dob,
                address=r.address,
                phone_number=r.phone_number,
                email=r.email,
                username=r.username,
                password=r.password,
            ) for r in rows
        ]
    


@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    with SessionLocal() as db:
        row = db.get(UserModel, user_id)
        if row is None:
            raise HTTPException(status_code=404, detail="User not found")
        return User(
            name=row.name,
            age=row.age,
            dob=row.dob,
            address=row.address,
            phone_number=row.phone_number,
            email=row.email,
            username=row.username,
            password=row.password,
        )



@app.patch("/users/{user_id}", response_model=User)
async def update_user(user_id: int, updates: Dict[str, Any]):
    # Fetch row
    with SessionLocal() as db:
        row = db.get(UserModel, user_id)
        if row is None:
            raise HTTPException(status_code=404, detail="User not found")
    # Username change is not supported in PATCH to keep things simple
    if "username" in updates:
        # Enforce uniqueness against others if username provided
        new_username = updates["username"]
        for i, user_data in enumerate(user_store):
            if user_data is not None and i != user_id and user_data.get("username") == new_username:
                raise HTTPException(status_code=409, detail="Target username already exists")
        # Allow updating username after uniqueness check

    # Validate phone number if provided
    if "phone_number" in updates and not is_phone_number_valid(str(updates["phone_number"])):
        raise HTTPException(status_code=422, detail="Invalid phone number. Digits only.")
    
    # Validate age if provided
    if "age" in updates:
        try:
            age_int = int(updates["age"])  # accept number or numeric string
        except (TypeError, ValueError):
            raise HTTPException(status_code=422, detail="Invalid age. Must be 1-99.")
        if not is_age_valid(age_int):
            raise HTTPException(status_code=422, detail="Invalid age. Must be 1-99.")

    # Validate dob if provided as string
    if "dob" in updates and isinstance(updates["dob"], str) and not is_dob_valid(updates["dob"]):
        raise HTTPException(status_code=422, detail="Invalid dob format. Use YYYY-MM-DD.")
    
    # Validate email if provided
    if "email" in updates and not is_email_valid(str(updates["email"])):
        raise HTTPException(status_code=422, detail="Invalid email format.")

    # Apply updates (only known fields)
    allowed_fields = {"name", "age", "dob", "address", "phone_number", "email", "password", "username"}
    for key, value in list(updates.items()):
        if key in allowed_fields:
            setattr(row, key, value)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise HTTPException(status_code=409, detail="Username or phone conflict")

        # refresh file mirror from same session
        rows = db.execute(select(UserModel)).scalars().all()
        global user_store
        user_store = [
            {
                "name": r.name,
                "age": r.age,
                "dob": r.dob,
                "address": r.address,
                "phone_number": r.phone_number,
                "email": r.email,
                "username": r.username,
                "password": r.password,
            }
            for r in rows
        ]
        save_users_to_file()

        return User(
            name=row.name,
            age=row.age,
            dob=row.dob,
            address=row.address,
            phone_number=row.phone_number,
            email=row.email,
            username=row.username,
            password=row.password,
        )


@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    with SessionLocal() as db:
        row = db.get(UserModel, user_id)
        if row is None:
            raise HTTPException(status_code=404, detail="User not found")
        db.delete(row)
        db.commit()
        # refresh file mirror
        rows = db.execute(select(UserModel)).scalars().all()
        global user_store
        user_store = [
            {
                "name": r.name,
                "age": r.age,
                "dob": r.dob,
                "address": r.address,
                "phone_number": r.phone_number,
                "email": r.email,
                "username": r.username,
                "password": r.password,
            }
            for r in rows
        ]
        save_users_to_file()
        return {"message": "Delete user successfully"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
