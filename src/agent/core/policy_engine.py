from datetime import datetime
from typing import List, Dict


class PolicyEngine:

    def __init__(self, policies: List[Dict]):
        self.policies = sorted(policies, key=lambda p: p["priority"])

    def evaluate(self, action: dict, order: dict, user: dict) -> dict:

        for policy in self.policies:
            pid = policy["id"]

            if pid == "fraud_flag_restriction":
                if user.get("fraud_flag"):
                    return {
                        "approved": False,
                        "reason": "Account flagged for suspicious activity.",
                        "triggered_policy": pid
                    }

            if pid == "high_value_identity_verification":
                if order["amount"] > policy["min_amount"]:
                    return {
                        "approved": False,
                        "requires_verification": True,
                        "reason": "Identity verification required.",
                        "triggered_policy": pid
                    }

            if pid == "no_cancel_after_shipping":
                if order["status"] in policy["blocked_statuses"]:
                    return {
                        "approved": False,
                        "reason": "Order already shipped.",
                        "triggered_policy": pid
                    }

            if pid == "standard_cancellation_window":
                age = datetime.now() - order["created_at"]
                if age.days >= policy["max_days"]:
                    return {
                        "approved": False,
                        "reason": "Cancellation window expired.",
                        "triggered_policy": pid
                    }

        return {"approved": True}
