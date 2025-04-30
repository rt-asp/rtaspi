#!/usr/bin/env python3
"""
Example of setting up a secure HTTPS server with RTASPI.
Demonstrates SSL certificate handling, authentication, and basic routing.
"""

import os
import yaml
import argparse
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt
import uvicorn

# Initialize FastAPI app
app = FastAPI(title="RTASPI HTTPS Server Example")
security = HTTPBearer()

# Load configuration
def load_config(config_path: str) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)

# JWT token validation
def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    try:
        payload = jwt.decode(
            credentials.credentials,
            config["auth"]["secret"],
            algorithms=["HS256"]
        )
        return payload
    except jwt.JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )

# Routes
@app.get("/")
async def root():
    return {"message": "RTASPI HTTPS Server Example"}

@app.get("/secure", dependencies=[Depends(verify_jwt_token)])
async def secure_endpoint():
    return {"message": "This is a secure endpoint"}

@app.post("/auth/token")
async def get_token(username: str, password: str):
    # In a real application, verify credentials against a database
    if username == "admin" and password == "secret":
        token = jwt.encode(
            {"sub": username},
            config["auth"]["secret"],
            algorithm="HS256"
        )
        return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(
        status_code=401,
        detail="Invalid username or password"
    )

def setup_cors(app: FastAPI, config: dict):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config["server"]["cors"]["origins"],
        allow_methods=config["server"]["cors"]["methods"],
        allow_headers=["*"],
        allow_credentials=True,
    )

def main():
    parser = argparse.ArgumentParser(description="RTASPI HTTPS Server Example")
    parser.add_argument("--config", type=str, default="server_config.yaml",
                       help="Path to server configuration file")
    args = parser.parse_args()

    # Load configuration
    global config
    config = load_config(args.config)

    # Setup CORS
    setup_cors(app, config)

    # Ensure SSL certificates exist
    cert_path = Path(config["server"]["ssl"]["cert"])
    key_path = Path(config["server"]["ssl"]["key"])
    
    if not cert_path.exists() or not key_path.exists():
        print("Error: SSL certificates not found. Please run generate_certs.sh first.")
        return

    # Start server
    uvicorn.run(
        app,
        host=config["server"]["host"],
        port=config["server"]["port"],
        ssl_keyfile=str(key_path),
        ssl_certfile=str(cert_path),
    )

if __name__ == "__main__":
    main()
