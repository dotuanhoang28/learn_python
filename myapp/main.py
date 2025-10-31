from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
import uvicorn
import datetime
import os
import json
import re
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

    new_user = {
        "name": user.name,
        "age": user.age,
        "dob": user.dob,
        "address": user.address,
        "phone_number": user.phone_number,
        "email": user.email,
        "username": user.username,
        "password": user.password,
    }

    user_store.append(new_user)
    save_users_to_file()
    return User(**new_user)
    

@app.get("/users", response_model=List[User])
async def list_users():
    result: List[User] = []
    for data in user_store:
        if data is not None:
            result.append(User(**data))
    return result
    


@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    if user_id < 0 or user_id >= len(user_store) or user_store[user_id] is None:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user_store[user_id])


# @app.put("/users/{user_id}", response_model=User)
# async def replace_user(user_id: int, user: User):
#     if user_id < 0 or user_id >= len(user_store) or user_store[user_id] is None:
#         raise HTTPException(status_code=404, detail="User not found")
#     # Username must be unique across other users
#     for i, record in enumerate(user_store):
#         if record is not None and i != user_id and record.get("username") == user.username:
#             raise HTTPException(status_code=409, detail="Target username already exists")
#     if not is_phone_number_valid(user.phone_number):
#         raise HTTPException(status_code=422, detail="Invalid phone number. Digits only.")
#     if not is_age_valid(user.age):
#         raise HTTPException(status_code=422, detail="Invalid age. Must be 1-99.")
#     if not is_dob_valid(user.dob):
#         raise HTTPException(status_code=422, detail="Invalid dob format. Use DD-MM-YYYY.")

#     user_store[user_id] = {
#         "name": user.name,
#         "age": user.age,
#         "dob": user.dob,
#         "address": user.address,
#         "phone_number": user.phone_number,
#         "username": user.username,
#         "password": user.password,
#     }
#     save_users_to_file()
#     return User(**user_store[user_id])


@app.patch("/users/{user_id}", response_model=User)
async def update_user(user_id: int, updates: Dict[str, Any]):
    if user_id < 0 or user_id >= len(user_store) or user_store[user_id] is None:
        raise HTTPException(status_code=404, detail="User not found")

    current = user_store[user_id]

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
            current[key] = value
    save_users_to_file()
    return User(**current)


@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    if user_id < 0 or user_id >= len(user_store) or user_store[user_id] is None:
        raise HTTPException(status_code=404, detail="User not found")
    # Mark as deleted without shifting IDs
    user_store[user_id] = None
    save_users_to_file()
    return {"message": "Delete user successfully"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
