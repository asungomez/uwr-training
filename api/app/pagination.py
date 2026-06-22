from typing import Annotated

from fastapi import Query
from pydantic import BaseModel

MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 10


class PaginationParams(BaseModel):
    """Query params for paginated list endpoints. Use as a FastAPI dependency."""

    page: Annotated[int, Query(ge=1)] = 1
    page_size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class Page[T](BaseModel):
    """A page of results plus the total count across all pages."""

    items: list[T]
    total_count: int


def paginate[T](items: list[T], params: PaginationParams) -> Page[T]:
    """Slice an already-materialized list. For endpoints that can't push
    LIMIT/OFFSET to SQL (e.g. merged/sorted results)."""
    start = params.offset
    return Page(items=items[start : start + params.page_size], total_count=len(items))
