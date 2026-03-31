from __future__ import annotations

from typing import Any


def success(data: Any) -> dict[str, Any]:
    return {"code": 0, "data": data, "message": "ok"}


def error_response(code: int, message: str) -> dict[str, Any]:
    return {"code": code, "data": None, "message": message}


def build_page(records: list[Any], page_num: int, page_size: int, total_row: int) -> dict[str, Any]:
    total_page = 0 if page_size <= 0 else (total_row + page_size - 1) // page_size
    return {
        "records": records,
        "pageNumber": page_num,
        "pageSize": page_size,
        "totalPage": total_page,
        "totalRow": total_row,
        "optimizeCountQuery": False,
    }
