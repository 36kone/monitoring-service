from datetime import datetime
from uuid import UUID

from pydantic import AliasPath, EmailStr, Field, field_validator

from app.schemas.base import BaseSchema


class CreateUser(BaseSchema):
    name: str
    email: EmailStr
    password: str
    phone: str
    single_session: bool | None = True
    mfa_enabled: bool | None = False

    @field_validator("password", mode="after")
    @classmethod
    def validate_password(cls, password: str) -> str:
        if len(password) < 5:
            raise ValueError("Password must be at least 5 characters long")
        return password


class UserSearchRequest(BaseSchema):
    keyword: str | None = None
    size: int = 10
    page: int = 1


class UserResponse(BaseSchema):
    id: UUID
    name: str
    email: str
    phone: str
    is_active: bool
    is_super_user: bool
    mfa_enabled: bool | None = None
    single_session: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: str | None = Field(default=None, validation_alias=AliasPath("who_created", "name"))
    updated_by: str | None = Field(default=None, validation_alias=AliasPath("who_updated", "name"))


class UpdateCurrentUser(BaseSchema):
    name: str
    email: str
    phone: str


class UpdateUser(BaseSchema):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    is_active: bool | None = None
    is_admin: bool | None = None
    mfa_enabled: bool | None = None
    single_session: bool | None = None


class SimpleUserResponse(BaseSchema):
    id: UUID
    name: str
    phone: str
    email: EmailStr
    is_super_user: bool
    is_admin: bool
