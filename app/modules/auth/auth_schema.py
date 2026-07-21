from pydantic import BaseModel, EmailStr, field_validator

from app.modules.user.user_schema import SimpleUserResponse
from app.schemas.base import BaseSchema


class Token(BaseSchema):
    access_token: str
    token_type: str
    user: SimpleUserResponse
    token_role: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    new_password: str
    token: str

    @field_validator("new_password", mode="after")
    @classmethod
    def validate_password(cls, password: str) -> str:
        if len(password) < 5:
            raise ValueError("Password must be at least 5 characters long")
        return password


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password", mode="after")
    @classmethod
    def validate_password(cls, password: str) -> str:
        if len(password) < 5:
            raise ValueError("Password must be at least 5 characters long")
        return password


class Message(BaseSchema):
    message: str


class Enable2FARequest(BaseModel):
    code: str


class VerifyUserByPassword(BaseSchema):
    password: str

    @field_validator("password", mode="after")
    @classmethod
    def validate_password(cls, password: str) -> str:
        if len(password) < 5:
            raise ValueError("Password must be at least 5 characters long")
        return password
