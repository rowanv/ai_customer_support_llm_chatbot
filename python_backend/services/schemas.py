from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict


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
    estimated_delivery: Optional[datetime] = None

    model_config = ConfigDict(extra="forbid")


class OrderModel(BaseModel):
    order_id: str
    customer_email: EmailStr
    status: str
    datetime_placed: Optional[datetime] = None
    shipments: List[Shipment] = []

    model_config = ConfigDict(extra="forbid")


class OkOrderResponse(BaseModel):
    ok: bool = True
    order: OrderModel


class ErrorResponse(BaseModel):
    ok: bool = False
    error: ErrorObj
