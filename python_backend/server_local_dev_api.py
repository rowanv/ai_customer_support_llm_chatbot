"""Local external orders API used for development and testing.

This module provides a tiny in-memory HTTP API that mimics the external
`/api/v1/orders/...` service. It's intended for local development and
component tests so the application can call an HTTP API instead of a live
third-party service.

In production this code would not be used; instead the service would call the
real external API over the network (or use a dedicated SDK). Keeping a small
local implementation here makes it simple to run the backend and agents in a
fully-local developer environment.
"""
import datetime
from datetime import date, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel


class Shipment(BaseModel):
    carrier: str
    tracking_number: str
    status: str
    estimated_delivery: Optional[str]


class OrderRecord(BaseModel):
    order_id: str
    customer_email: str
    status: str
    datetime_placed: Optional[str]
    shipments: List[Shipment]


class OrderUpdate(BaseModel):
    status: Optional[str]


# Lightweight in-memory datastore for local testing
ORDERS_DB: Dict[str, OrderRecord] = {
    "A123": OrderRecord(
        order_id="A123",
        customer_email="a123@gmail.com",
        status="shipped",
        tracking_status="shipped",
        datetime_placed="2026-02-18T10:00:00Z",
        shipments=[
            Shipment(
                carrier="UPS",
                tracking_number="1Z999AA10123456784",
                status="in_transit",
                estimated_delivery=str(date(2026, 2, 22)),
            )
        ],
    ),

    # Add a non-shipped order for testing cancellation and other flows
    "B456": OrderRecord(
        order_id="B456",
        customer_email="b456@gmail.com",
        status="processing",
        datetime_placed=datetime.datetime.now(timezone.utc).isoformat(),
        shipments=[],
    ),
}


router = APIRouter()


def _get_record_for_order(order_id: str, x_customer_email: Optional[str]) -> OrderRecord:
    """Helper to validate header, existence, and ownership of an order.

    Raises the appropriate `HTTPException` on failure and returns the `OrderRecord`
    when checks pass.
    """
    if x_customer_email is None:
        raise HTTPException(status_code=400, detail="Missing X-Customer-Email header")

    record = ORDERS_DB.get(order_id)
    if record is None:
        raise HTTPException(status_code=404, detail="order not found")

    if record.customer_email.lower() != x_customer_email.lower():
        raise HTTPException(status_code=403, detail="email does not match order")

    return record


@router.get("/api/v1/orders/{order_id}/", response_model=OrderRecord)
async def get_order(order_id: str, x_customer_email: Optional[str] = Header(None)):
    """Return an order record if the X-Customer-Email header matches.

    - 400 if the header is missing
    - 404 if the order_id is not present
    - 403 if the email does not match the order's owner
    - 200 with the order record if matched
    """
    return _get_record_for_order(order_id, x_customer_email)


@router.patch("/api/v1/orders/{order_id}/", response_model=OrderRecord)
async def patch_order(order_id: str, update: OrderUpdate, x_customer_email: Optional[str] = Header(None)):
    """Patch an order record. Only supports updating `status` for local testing.

    - 400 if the header is missing
    - 404 if the order_id is not present
    - 403 if the email does not match the order's owner
    - 200 with the updated order record
    """
    record = _get_record_for_order(order_id, x_customer_email)

    if update.status:
        record.status = update.status

    ORDERS_DB[order_id] = record
    return record


def register_local_external_api(app):
    app.include_router(router)
