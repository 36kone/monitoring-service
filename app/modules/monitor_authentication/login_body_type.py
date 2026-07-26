from enum import StrEnum


class LoginBodyType(StrEnum):
    JSON = "json"
    FORM_URLENCODED = "form_urlencoded"
    MULTIPART = "multipart"
