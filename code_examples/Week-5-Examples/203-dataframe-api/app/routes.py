"""Route layer — thin HTTP wrappers that delegate to the service layer.

Routes handle URLs, query params, and HTTP status codes only. All the actual
pandas work is in services.py.
"""

from fastapi import APIRouter, Query

from . import services
from .models import CategoryAgg, PagedOrders, Summary

router = APIRouter()


@router.get("/summary", response_model=Summary)
def get_summary():
    """Dataset-wide totals."""
    return services.summary()


@router.get("/by-category", response_model=list[CategoryAgg])
def get_by_category():
    """Revenue aggregated per product category."""
    return services.by_category()


@router.get("/orders", response_model=PagedOrders)
def get_orders(
    limit: int = Query(10, ge=1, le=100, description="rows per page"),
    offset: int = Query(0, ge=0, description="rows to skip"),
    region: str | None = Query(None, description="filter by region, e.g. East"),
):
    """Raw orders, paginated, with optional ?region= filter."""
    return services.orders_page(limit=limit, offset=offset, region=region)
