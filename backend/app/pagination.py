from fastapi import Query
from sqlalchemy.orm import Query as SAQuery


def paginate_params(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
):
    return {"page": page, "page_size": page_size}


def paginate_query(query: SAQuery, page: int, page_size: int) -> dict:
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }
