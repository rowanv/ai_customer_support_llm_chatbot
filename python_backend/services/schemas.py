from __future__ import annotations

from pydantic import BaseModel
from typing import Any, Dict, List, Optional


class ErrorObj(BaseModel):
    type: str
    detail: Optional[Any] = None
    status: Optional[int] = None
    redirect: Optional[str] = None
    message: Optional[str] = None


class Shipment(BaseModel):
    carrier: str
    tracking_number: str
    status: str
    estimated_delivery: Optional[str]


class OrderModel(BaseModel):
    order_id: str
    customer_email: str
    status: str
    datetime_placed: Optional[str]
    shipments: List[Dict[str, Any]] = []


class OkOrderResponse(BaseModel):
    ok: bool = True
    order: OrderModel


class ErrorResponse(BaseModel):
    ok: bool = False
    error: ErrorObj
