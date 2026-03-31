from __future__ import annotations

from pydantic import BaseModel


class DeleteRequest(BaseModel):
    id: int
