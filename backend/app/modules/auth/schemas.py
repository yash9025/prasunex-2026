"""Authentication request and response schemas."""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    """User credentials for token issuance."""

    email: EmailStr = Field(..., json_schema_extra={"example": "priya.sharma@demo.learningbridge.internal"})
    password: str = Field(..., min_length=6, json_schema_extra={"example": "TeacherPass123!"})


class UserOut(BaseModel):
    """User profile data."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: str
    is_active: bool


class SchoolMembershipOut(BaseModel):
    """Active membership context in a school."""

    model_config = ConfigDict(from_attributes=True)

    school_id: str
    school_name: str
    school_code: str
    role: str


class MeResponse(BaseModel):
    """Current authenticated actor, active tenant, and permitted scope per Section 7.1."""

    id: str
    email: str
    full_name: str
    active_school_id: str
    active_school_name: str
    role: str
    memberships: List[SchoolMembershipOut]
    authorized_class_ids: List[str]


class TokenResponse(BaseModel):
    """Signed JWT access token envelope."""

    access_token: str
    token_type: str = "Bearer"
    expires_in_minutes: int
    user: UserOut
    active_school: SchoolMembershipOut
