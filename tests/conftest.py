import pytest
from datetime import datetime, timedelta


@pytest.fixture
def sample_order():
    return {
        "order_id": "123",
        "created_at": datetime.now() - timedelta(days=5),
        "status": "processing",
        "amount": 200
    }


@pytest.fixture
def sample_baseline_policy():
    return [
        {
            "id": "standard_cancellation_window",
            "max_days": 10,
            "priority": 3
        }
    ]


@pytest.fixture
def sample_user_flagged_policy():
    return[
        {
            "id": "fraud_flag_restriction",
            "type": "fraud_block",
            "block_actions": ["cancel_order"],
            "priority": 0
        }
    ]
