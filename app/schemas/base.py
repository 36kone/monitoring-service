from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator


def to_camel(string: str) -> str:
    parts = string.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    __allow_empty_strings__ = {"keyword"}

    @model_validator(mode="before")
    @classmethod
    def validate_empty_strings(cls, values: Any):
        if isinstance(values, dict):
            for field, value in values.items():
                if field in cls.__allow_empty_strings__:
                    continue

                if isinstance(value, str) and value.strip() == "":
                    raise ValueError(f"The field '{field}' cannot be an empty string.")

        return values
