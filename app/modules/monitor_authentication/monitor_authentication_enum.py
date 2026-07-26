from enum import StrEnum


class MonitorAuthenticationTypeEnum(StrEnum):
    NONE = "none"
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"
    BASIC = "basic"
    DYNAMIC_LOGIN = "dynamic_login"
