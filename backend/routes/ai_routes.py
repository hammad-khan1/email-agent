"""AI assistant and email generation routes."""
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.ai.ai_service import generate_personalized_email, ai_assistant_chat, rewrite_email

router = APIRouter()


class GenerateEmailRequest(BaseModel):
    name: str
    email: str
    domain: Optional[str] = None
    position: Optional[str] = None
    joining_date: Optional[str] = None
    company: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    tone: str = "Professional and Friendly"
    length: str = "Short"
    extra_instruction: Optional[str] = None


class AssistantRequest(BaseModel):
    message: str
    context: Optional[str] = None


class RewriteRequest(BaseModel):
    original: str
    instruction: str


@router.post("/generate-email")
async def generate_email(req: GenerateEmailRequest):
    try:
        result = generate_personalized_email(**req.model_dump())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assistant")
async def assistant(req: AssistantRequest):
    try:
        response = ai_assistant_chat(req.message, req.context)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rewrite")
async def rewrite(req: RewriteRequest):
    try:
        result = rewrite_email(req.original, req.instruction)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
