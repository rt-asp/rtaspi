#!/usr/bin/env python3
"""
Example of creating a REST API with RTASPI.
Demonstrates OpenAPI documentation, authentication, and rate limiting.
"""

import argparse
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import jwt
import time
import uvicorn
from rtaspi.web.api import APIBase

# Models
class Device(BaseModel):
    id: str
    name: str
    type: str
    status: str
    last_seen: datetime

class Stream(BaseModel):
    id: str
    device_id: str
    url: str
    status: str
    resolution: str
    fps: int

class User(BaseModel):
    username: str
    disabled: Optional[bool] = None

class Token(BaseModel):
    access_token: str
    token_type: str

# API Configuration
SECRET_KEY = "your-secret-key-here"  # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Rate limiting configuration
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_REQUESTS = 100
rate_limit_store = {}  # {ip: [(timestamp, count)]}

# Mock database
devices_db = {
    "dev1": Device(
        id="dev1",
        name="Camera 1",
        type="camera",
        status="online",
        last_seen=datetime.now()
    )
}

streams_db = {
    "stream1": Stream(
        id="stream1",
        device_id="dev1",
        url="rtsp://example.com/stream1",
        status="active",
        resolution="1920x1080",
        fps=30
    )
}

users_db = {
    "admin": {
        "username": "admin",
        "hashed_password": "hashed_secret",  # In production, use proper hashing
        "disabled": False
    }
}

# Initialize FastAPI
app = FastAPI(
    title="RTASPI REST API Example",
    description="Example REST API demonstrating RTASPI capabilities",
    version="1.0.0"
)

# Security
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    now = time.time()
    
    # Clean old entries
    if client_ip in rate_limit_store:
        rate_limit_store[client_ip] = [
            (ts, count) for ts, count in rate_limit_store[client_ip]
            if now - ts < RATE_LIMIT_WINDOW
        ]
    
    # Check rate limit
    current_window = rate_limit_store.get(client_ip, [])
    total_requests = sum(count for _, count in current_window)
    
    if total_requests >= RATE_LIMIT_MAX_REQUESTS:
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests"}
        )
    
    # Update rate limit store
    if not current_window:
        rate_limit_store[client_ip] = [(now, 1)]
    else:
        rate_limit_store[client_ip].append((now, 1))
    
    return await call_next(request)

# Authentication
def create_access_token(data: dict):
    expires = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = data.copy()
    to_encode.update({"exp": expires})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        if username not in users_db:
            raise HTTPException(status_code=401, detail="User not found")
        return User(**users_db[username])
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

# Routes
@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users_db.get(form_data.username)
    if not user or form_data.password != "secret":  # In production, use proper password verification
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token({"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/devices/", response_model=List[Device])
async def list_devices(_: User = Depends(get_current_user)):
    return list(devices_db.values())

@app.get("/devices/{device_id}", response_model=Device)
async def get_device(device_id: str, _: User = Depends(get_current_user)):
    if device_id not in devices_db:
        raise HTTPException(status_code=404, detail="Device not found")
    return devices_db[device_id]

@app.get("/streams/", response_model=List[Stream])
async def list_streams(_: User = Depends(get_current_user)):
    return list(streams_db.values())

@app.get("/streams/{stream_id}", response_model=Stream)
async def get_stream(stream_id: str, _: User = Depends(get_current_user)):
    if stream_id not in streams_db:
        raise HTTPException(status_code=404, detail="Stream not found")
    return streams_db[stream_id]

@app.get("/status")
async def get_status(_: User = Depends(get_current_user)):
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "devices_count": len(devices_db),
        "streams_count": len(streams_db)
    }

def main():
    parser = argparse.ArgumentParser(description="RTASPI REST API Example")
    parser.add_argument("--port", type=int, default=8080,
                       help="Port to run the server on")
    args = parser.parse_args()
    
    uvicorn.run(app, host="0.0.0.0", port=args.port)

if __name__ == "__main__":
    main()
