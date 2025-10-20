from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn
from typing import Optional
import os

app = FastAPI(title="Login Web App")

# Create templates directory if it doesn't exist
if not os.path.exists("templates"):
    os.makedirs("templates")

# Create static directory if it doesn't exist  
if not os.path.exists("static"):
    os.makedirs("static")

templates = Jinja2Templates(directory="templates")

# Mock user database (in a real app, this would be a proper database)
USERS_DB = {
    "admin": "password123",
    "user": "mypassword",
    "demo": "demo123"
}

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    """Display the login form"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    """Handle login authentication"""
    if username in USERS_DB and USERS_DB[username] == password:
        return templates.TemplateResponse("success.html", {
            "request": request, 
            "username": username
        })
    else:
        return templates.TemplateResponse("login.html", {
            "request": request, 
            "error": "Invalid username or password"
        })

@app.get("/success")
async def success_page(request: Request):
    """Success page after login"""
    return templates.TemplateResponse("success.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

