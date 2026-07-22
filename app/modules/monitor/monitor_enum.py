from enum import StrEnum


class MonitorStatusEnum(StrEnum):
    UNKNOWN = "unknown"
    UP = "up"
    DOWN = "down"
    DEGRADED = "degraded"
