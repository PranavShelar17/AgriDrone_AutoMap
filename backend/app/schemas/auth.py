import uuid
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str = Field(..., description="Registered user email address")
    password: str = Field(..., min_length=6, description="User password")


class UserProfileResponse(BaseModel):
    id: uuid.UUID = Field(..., description="User unique identifier")
    email: str = Field(..., description="User email address")
    full_name: str = Field(..., description="User full name")
    role: str = Field(..., description="Assigned role: ADMIN, AGRONOMIST, FARMER")
    is_active: bool = Field(..., description="Account active status")
    assigned_farm_ids: List[uuid.UUID] = Field(default_factory=list, description="IDs of farms owned/assigned to this user")
    created_at: datetime = Field(..., description="Account creation timestamp")

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="Signed JWT Bearer token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token lifespan in seconds")
    user: UserProfileResponse = Field(..., description="Authenticated user profile")


class FarmerCreateRequest(BaseModel):
    email: str = Field(..., description="Farmer email address")
    password: str = Field(..., min_length=8, description="Initial password (min 8 chars)")
    full_name: str = Field(..., min_length=2, max_length=150, description="Farmer full name")
    farm_id: Optional[uuid.UUID] = Field(default=None, description="Optional existing farm ID to assign to this farmer")


class FarmerAssignFarmRequest(BaseModel):
    farmer_id: uuid.UUID = Field(..., description="User ID of the farmer")
    farm_id: uuid.UUID = Field(..., description="Farm ID to assign")


class AccountStatusUpdateRequest(BaseModel):
    is_active: bool = Field(..., description="Set active (true) or disabled (false)")
