from datetime import datetime

import pytest
from pydantic import ValidationError

from python_backend.services.schemas import OrderModel


def make_base_order():
    return {
        "order_id": "xyz",
        "customer_email": "test@example.com",
        "status": "processing",
        "datetime_placed": datetime.now().isoformat(),
        "shipments": [],
    }


def test_ordermodel_accepts_valid_email():
    data = make_base_order()
    # should not raise
    order = OrderModel.model_validate(data)
    assert order.customer_email == "test@example.com"


def test_ordermodel_rejects_invalid_email():
    data = make_base_order()
    data["customer_email"] = "not-an-email"
    with pytest.raises(ValidationError):
        OrderModel.model_validate(data)
