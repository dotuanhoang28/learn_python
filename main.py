from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
import uvicorn
import datetime


app = FastAPI(title="Basic User CRUD API")


class User(BaseModel):
    name: str
    dob: datetime.date = Field(..., description="Date of Birth (YYYY-MM-DD)")
    address: str
    phone_number: str
    username: str
    # Keep password required for input, but exclude from all responses
    password: str = Field(..., exclude=True)


# In-memory store (username -> user dict)
user_store: Dict[str, Dict] = {}


def is_phone_number_valid(phone_number: str) -> bool:
    return phone_number.isdigit()

# ===== JSON API: CRUD =====

@app.post("/users", response_model=User, status_code=201)
async def create_user(payload: User):
    if payload.username in user_store:
        raise HTTPException(status_code=409, detail="Username already exists")
    if not is_phone_number_valid(payload.phone_number):
        raise HTTPException(status_code=422, detail="Invalid phone number. Digits only.")

    user_store[payload.username] = {
        "name": payload.name,
        "dob": payload.dob,
        "address": payload.address,
        "phone_number": payload.phone_number,
        "username": payload.username,
        "password": payload.password,
    }
    return User(**user_store[payload.username])
    

@app.get("/users", response_model=List[User])
async def list_users():
    result: List[User] = []
    for data in user_store.values():
        result.append(User(**data))
    return result
    


@app.get("/users/{username}", response_model=User)
async def get_user(username: str):
    if username not in user_store:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user_store[username])


@app.put("/users/{username}", response_model=User)
async def replace_user(username: str, payload: User):
    if username != payload.username and payload.username in user_store:
        raise HTTPException(status_code=409, detail="Target username already exists")
    if not is_phone_number_valid(payload.phone_number):
        raise HTTPException(status_code=422, detail="Invalid phone number. Digits only.")

    # If username changes, move record
    if username in user_store and username != payload.username:
        del user_store[username]

    user_store[payload.username] = {
        "name": payload.name,
        "dob": payload.dob,
        "address": payload.address,
        "phone_number": payload.phone_number,
        "username": payload.username,
        "password": payload.password,
    }
    return User(**user_store[payload.username])


@app.patch("/users/{username}", response_model=User)
async def update_user(username: str, payload: Dict[str, Any]):
    if username not in user_store:
        raise HTTPException(status_code=404, detail="User not found")

    current = user_store[username]

    # Username change is not supported in PATCH to keep things simple
    if "username" in payload:
        payload.pop("username")

    # Validate phone number if provided
    if "phone_number" in payload and not is_phone_number_valid(str(payload["phone_number"])):
        raise HTTPException(status_code=422, detail="Invalid phone number. Digits only.")

    # If dob is provided as string, parse to date
    if "dob" in payload and isinstance(payload["dob"], str):
        try:
            payload["dob"] = datetime.date.fromisoformat(payload["dob"]) 
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid dob format. Use YYYY-MM-DD.")

    # Apply updates (only known fields)
    allowed_fields = {"name", "dob", "address", "phone_number", "password"}
    for key, value in list(payload.items()):
        if key in allowed_fields:
            current[key] = value

    return User(**current)


@app.delete("/users/{username}", status_code=204)
async def delete_user(username: str):
    if username not in user_store:
        raise HTTPException(status_code=404, detail="User not found")
    del user_store[username]
    return


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
