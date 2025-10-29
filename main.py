from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
import uvicorn
import datetime


app = FastAPI(title="Basic User CRUD API")


class User(BaseModel):
    name: str
    age: int
    dob: str
    address: str
    phone_number: str
    username: str
    password: str = Field(..., exclude=True)


# In-memory store as indexable list by numeric ID. Use None for deleted slots to keep IDs stable.
user_store: List[Optional[Dict[str, Any]]] = []


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
        datetime.date.fromisoformat(dob)
        return True
    except ValueError:
        return False
# ===== JSON API: CRUD =====

@app.post("/users", response_model=User, status_code=201)
async def create_user(payload: User):
    # Enforce unique username
    for record in user_store:
        if record is not None and record.get("username") == payload.username:
            raise HTTPException(status_code=409, detail="Username already exists")
    if not is_phone_number_valid(payload.phone_number):
        raise HTTPException(status_code=422, detail="Invalid phone number. Digits only.")
    if not is_age_valid(payload.age):
        raise HTTPException(status_code=422, detail="Invalid age. Must be 1-99.")
    if not is_dob_valid(payload.dob):
        raise HTTPException(status_code=422, detail="Invalid dob format. Use DD-MM-YYYY.")

    new_record = {
        "name": payload.name,
        "age": payload.age,
        "dob": payload.dob,
        "address": payload.address,
        "phone_number": payload.phone_number,
        "username": payload.username,
        "password": payload.password,
    }

    # Reuse first deleted slot if available, else append
    inserted_id: Optional[int] = None
    for i, record in enumerate(user_store):
        if record is None:
            user_store[i] = new_record
            inserted_id = i
            break
    if inserted_id is None:
        user_store.append(new_record)
        inserted_id = len(user_store) - 1

    return User(**new_record)
    

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


@app.put("/users/{user_id}", response_model=User)
async def replace_user(user_id: int, payload: User):
    if user_id < 0 or user_id >= len(user_store) or user_store[user_id] is None:
        raise HTTPException(status_code=404, detail="User not found")
    # Username must be unique across other users
    for i, record in enumerate(user_store):
        if record is not None and i != user_id and record.get("username") == payload.username:
            raise HTTPException(status_code=409, detail="Target username already exists")
    if not is_phone_number_valid(payload.phone_number):
        raise HTTPException(status_code=422, detail="Invalid phone number. Digits only.")
    if not is_age_valid(payload.age):
        raise HTTPException(status_code=422, detail="Invalid age. Must be 1-99.")
    if not is_dob_valid(payload.dob):
        raise HTTPException(status_code=422, detail="Invalid dob format. Use DD-MM-YYYY.")

    user_store[user_id] = {
        "name": payload.name,
        "age": payload.age,
        "dob": payload.dob,
        "address": payload.address,
        "phone_number": payload.phone_number,
        "username": payload.username,
        "password": payload.password,
    }
    return User(**user_store[user_id])


@app.patch("/users/{user_id}", response_model=User)
async def update_user(user_id: int, payload: Dict[str, Any]):
    if user_id < 0 or user_id >= len(user_store) or user_store[user_id] is None:
        raise HTTPException(status_code=404, detail="User not found")

    current = user_store[user_id]

    # Username change is not supported in PATCH to keep things simple
    if "username" in payload:
        # Enforce uniqueness against others if username provided
        new_username = payload["username"]
        for i, record in enumerate(user_store):
            if record is not None and i != user_id and record.get("username") == new_username:
                raise HTTPException(status_code=409, detail="Target username already exists")
        # Allow updating username after uniqueness check

    # Validate phone number if provided
    if "phone_number" in payload and not is_phone_number_valid(str(payload["phone_number"])):
        raise HTTPException(status_code=422, detail="Invalid phone number. Digits only.")
    
    # Validate age if provided
    if "age" in payload and not is_age_valid(str(payload["age"])):
        raise HTTPException(status_code=422, detail="Invalid age. Must be 1-99.")

    # Validate dob if provided as string
    if "dob" in payload and isinstance(payload["dob"], str) and not is_dob_valid(payload["dob"]):
        raise HTTPException(status_code=422, detail="Invalid dob format. Use DD-MM-YYYY.")

    # Apply updates (only known fields)
    allowed_fields = {"name", "age", "dob", "address", "phone_number", "password", "username"}
    for key, value in list(payload.items()):
        if key in allowed_fields:
            current[key] = value

    return User(**current)


@app.delete("/users/{user_id}", status_code=204)
async def delete_user(user_id: int):
    if user_id < 0 or user_id >= len(user_store) or user_store[user_id] is None:
        raise HTTPException(status_code=404, detail="User not found")
    # Mark as deleted without shifting IDs
    user_store[user_id] = None
    return


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
