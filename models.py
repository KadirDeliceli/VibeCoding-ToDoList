from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Todo:
    id: int
    title: str
    completed: bool
    created_at: str
    category_id: int
    time_range: str | None = None

    @classmethod
    def from_row(cls, row) -> "Todo":
        if len(row) == 6:
            id_, title, completed, created_at, category_id, time_range = row
        else:
            id_, title, completed, created_at, category_id = row
            time_range = None
        return cls(
            id=id_,
            title=title,
            completed=bool(completed),
            created_at=created_at,
            category_id=category_id,
            time_range=time_range,
        )
