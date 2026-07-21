from datetime import datetime

from .base import BaseSchema


class HealthResponse(BaseSchema):
    client_ip: str
    server_ip: str
    current_date_time: datetime
    api_version: str
    database_alive: bool
    message: str
