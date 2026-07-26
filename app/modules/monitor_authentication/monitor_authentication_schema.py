from uuid import UUID

from pydantic import AnyHttpUrl, Field, model_validator

from app.schemas.base import BaseSchema

from .login_body_type import LoginBodyType
from .monitor_authentication_enum import MonitorAuthenticationTypeEnum


class MonitorAuthenticationPayload(BaseSchema):
    api_key: str | None = None
    token: str | None = None
    username: str | None = None
    password: str | None = None
    header_name: str | None = None
    login_body: dict | None = None
    login_headers: dict[str, str] | None = None


class CreateMonitorAuthentication(BaseSchema):
    auth_type: MonitorAuthenticationTypeEnum
    credentials: MonitorAuthenticationPayload = Field(default_factory=MonitorAuthenticationPayload)
    login_url: AnyHttpUrl | None = None
    login_method: str = "POST"
    login_body_type: LoginBodyType = LoginBodyType.JSON
    token_json_path: str | None = None
    expires_in_json_path: str | None = None
    expires_at_json_path: str | None = None
    authorization_header: str = "Authorization"
    authorization_scheme: str = "Bearer"
    refresh_skew_seconds: int = Field(default=60, ge=0, le=3600)

    @model_validator(mode="after")
    def validate_configuration(self):
        if self.auth_type is MonitorAuthenticationTypeEnum.DYNAMIC_LOGIN and not self.login_url:
            raise ValueError("loginUrl is required for dynamic login")
        if self.auth_type is MonitorAuthenticationTypeEnum.API_KEY and not self.credentials.api_key:
            raise ValueError("credentials.apiKey is required for API key authentication")
        if self.auth_type is MonitorAuthenticationTypeEnum.BEARER_TOKEN and not self.credentials.token:
            raise ValueError("credentials.token is required for bearer authentication")
        if self.auth_type is MonitorAuthenticationTypeEnum.BASIC and (
            not self.credentials.username or not self.credentials.password
        ):
            raise ValueError("credentials.username and credentials.password are required for basic auth")
        return self


class UpdateMonitorAuthentication(CreateMonitorAuthentication):
    pass


class MonitorAuthenticationResponse(BaseSchema):
    id: UUID
    monitor_id: UUID
    auth_type: MonitorAuthenticationTypeEnum
    configured: bool
    login_url: str | None
    login_method: str | None
    login_body_type: LoginBodyType
    token_json_path: str | None
    expires_in_json_path: str | None
    expires_at_json_path: str | None
    authorization_header: str
    authorization_scheme: str
    refresh_skew_seconds: int
