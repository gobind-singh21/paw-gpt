from app.config import ACCESS_TOKEN_EXPIRE_MINUTES
from app.config import REFRESH_TOKEN_EXPIRE_DAYS
from app.utils import create_jwt
from app.utils import PasswordManager
from app.utils import verify_jwt
from datetime import timedelta
from fastapi import APIRouter
from fastapi import Cookie
from fastapi import HTTPException
from fastapi import Request
from fastapi import Response
from fastapi import status
from pydantic import BaseModel
from typing import Optional

import asyncpg

router = APIRouter()

class UserRegisterationRequest(BaseModel):
	username: str
	password: str

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserRegisterationRequest, request: Request):
    pool: asyncpg.Pool = request.app.state.db_pool
    hashed_pwd = PasswordManager.hash_password(user_data.password)
    try:
        async with pool.acquire() as connection:
            await connection.execute(
				"INSERT INTO users(username, hashed_password) VALUES ($1, $2)",
				user_data.username,
				hashed_pwd
			)
        return {"message": "User registered successfully"}
    except asyncpg.UniqueViolationError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

@router.post("/login")
async def login(login_data: LoginRequest, request: Request, response: Response):
    pool: asyncpg.Pool = request.app.state.db_pool
    async with pool.acquire() as connection:
        user_record = await connection.fetchrow(
			"SELECT username, hashed_password FROM users WHERE username = $1",
			login_data.username
		)
    
    if not user_record:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    
    stored_hash = user_record["hashed_password"]
    is_valid = PasswordManager.verify_password(login_data.password, stored_hash)
    
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    
    user_payload = {"sub": login_data.username}
    
    access_token = create_jwt(user_payload, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES), "access")
    refresh_token = create_jwt(user_payload, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS), "refresh")
    
    response.set_cookie(
		key="refresh_token",
		value=refresh_token,
		httponly=True,
		samesite="strict",
		secure=False,
		max_age=REFRESH_TOKEN_EXPIRE_DAYS * 86400
	)
    
    response.set_cookie(
		key="access_token",
		value=access_token,
		httponly=True,
		samesite="strict",
		secure=False,
		max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
	)
    
    return {"message": "Login successful", "username": user_record["username"]}

@router.post("/refresh")
async def refresh_session(response: Response, refresh_token: Optional[str] = Cookie(None)):
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired or missing. Please log in again.")
    
    payload = verify_jwt(refresh_token, expected_type="refresh")
    username = payload.get("sub")
    user_payload = {"sub": username}
    
    new_access_token = create_jwt(user_payload, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES), "access")
    
    response.set_cookie(
		key="access_token",
		value=new_access_token,
		httponly=True,
		samesite="strict",
		secure=False,
		max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
	)
    
    return {"status": "session_refreshed", "user": username}