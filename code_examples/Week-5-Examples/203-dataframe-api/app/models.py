"""Pydantic response models — the shapes this API returns.

Keeping these here (the `models` layer) documents the API contract and powers
the auto-generated schema at /docs. The routes reference them via
`response_model=...`.
"""

from pydantic import BaseModel


class Summary(BaseModel):
    orders: int
    total_revenue: float
    avg_order_revenue: float
    customers: int


class CategoryAgg(BaseModel):
    category: str
    orders: int
    total_revenue: float
    avg_revenue: float


class OrderRecord(BaseModel):
    order_id: int
    order_date: str
    customer: str
    region: str
    category: str
    quantity: int
    unit_price: float
    revenue: float


class PagedOrders(BaseModel):
    total: int
    limit: int
    offset: int
    results: list[OrderRecord]
