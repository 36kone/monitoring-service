import builtins

from app.schemas.base import BaseSchema


class Pagination(BaseSchema):
    total: int
    size: int
    current: int
    pages: int
    previous: bool | None
    next: bool | None


class PaginatedResponse[T](BaseSchema):
    pagination: Pagination
    list: list[T]

    @classmethod
    def create(
        cls,
        *,
        total: int,
        page: int,
        size: int,
        items: builtins.list[T],
    ) -> "PaginatedResponse[T]":
        pages = (total // size) + (1 if total % size > 0 else 0)
        previous = page > 1
        next_ = page < pages

        pagination = Pagination(
            total=total,
            size=size,
            current=page,
            pages=pages,
            previous=previous,
            next=next_,
        )

        return cls(pagination=pagination, list=items)
