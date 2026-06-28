"""Auth API routes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.auth.auth_service import verify_credentials, create_token

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    if not verify_credentials(req.username, req.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(req.username)
    return LoginResponse(access_token=token, username=req.username)
