from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
import re


class ContactRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=10, max_length=20)
    email: EmailStr
    comment: Optional[str] = Field(None, max_length=1000)

    @field_validator("name")
    def validate_name(cls, v: str):
        if not re.match(r"^[a-zA-Zа-яА-ЯёЁ\s\-]+$", v):
            raise ValueError("Name must contain only letters, spaces, and hyphens")
        return v.strip()

    @field_validator("phone")
    def validate_phone(cls, v: str):
        # Remove all non-digit characters for validation
        cleaned = re.sub(r"\D", "", v)
        if len(cleaned) < 10:
            raise ValueError("Phone number must have at least 10 digits")
        # Format phone to international format if possible
        if cleaned.startswith("8") and len(cleaned) == 11:
            cleaned = "7" + cleaned[1:]
        return "+" + cleaned if not v.startswith("+") else v

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "phone": "+1234567890",
                "email": "john@example.com",
                "comment": "I need a website for my business",
            }
        }


class ContactResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
    ai_analysis: Optional[dict] = None


class AIAnalysis(BaseModel):
    sentiment: str
    priority: str
    category: str
    auto_reply_suggestion: str
