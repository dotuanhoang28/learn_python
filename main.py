from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
import uvicorn
import datetime


app = FastAPI(title="Basic User CRUD API")


class UserCreate(BaseModel):
    name: str
    dob: datetime.date = Field(..., description="Date of Birth (YYYY-MM-DD)")
    address: str
    phone_number: str
    username: str
    password: str


class UserOut(BaseModel):
    name: str
    dob: datetime.date
    address: str
    phone_number: str
    username: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    dob: Optional[datetime.date] = None
    address: Optional[str] = None
    phone_number: Optional[str] = None
    password: Optional[str] = None


# In-memory store (username -> user dict)
user_store: Dict[str, Dict] = {}


def is_phone_number_valid(phone_number: str) -> bool:
    return phone_number.isdigit()

# ===== JSON API: CRUD =====

@app.post("/users", response_model=UserOut, status_code=201)
async def create_user(payload: UserCreate):
    if payload.username in user_store:
        raise HTTPException(status_code=409, detail="Username already exists")
    if not is_phone_number_valid(payload.phone_number):
        raise HTTPException(status_code=422, detail="Invalid phone number. Digits only.")

    user_store[payload.username] = payload.model_dump()
    # Do not expose password in response
    stored = user_store[payload.username].copy()
    stored.pop("password", None)
    return UserOut(**stored)
    

@app.get("/users", response_model=List[UserOut])
async def list_users():
    result: List[UserOut] = []
    for data in user_store.values():
        copy_data = data.copy()
        copy_data.pop("password", None)
        result.append(UserOut(**copy_data))
    return result
    


@app.get("/users/{username}", response_model=UserOut)
async def get_user(username: str):
    if username not in user_store:
        raise HTTPException(status_code=404, detail="User not found")
    data = user_store[username].copy()
    data.pop("password", None)
    return UserOut(**data)


@app.put("/users/{username}", response_model=UserOut)
async def replace_user(username: str, payload: UserCreate):
    if username != payload.username and payload.username in user_store:
        raise HTTPException(status_code=409, detail="Target username already exists")
    if not is_phone_number_valid(payload.phone_number):
        raise HTTPException(status_code=422, detail="Invalid phone number. Digits only.")

    # If username changes, move record
    if username in user_store and username != payload.username:
        del user_store[username]

    user_store[payload.username] = payload.model_dump()
    data = user_store[payload.username].copy()
    data.pop("password", None)
    return UserOut(**data)


@app.patch("/users/{username}", response_model=UserOut)
async def update_user(username: str, payload: UserUpdate):
    if username not in user_store:
        raise HTTPException(status_code=404, detail="User not found")

    current = user_store[username]

    update_data = payload.model_dump(exclude_unset=True)
    # Username change is not supported in PATCH to keep things simple
    if "username" in update_data:
        update_data.pop("username")

    # Validate phone number if provided
    if "phone_number" in update_data and not is_phone_number_valid(str(update_data["phone_number"])):
        raise HTTPException(status_code=422, detail="Invalid phone number. Digits only.")

    current.update(update_data)
    data = current.copy()
    data.pop("password", None)
    return UserOut(**data)


@app.delete("/users/{username}", status_code=204)
async def delete_user(username: str):
    if username not in user_store:
        raise HTTPException(status_code=404, detail="User not found")
    del user_store[username]
    return


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
