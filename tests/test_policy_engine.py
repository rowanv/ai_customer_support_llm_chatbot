from agent.core.policy_engine import PolicyEngine


def test_standard_cancellation_allowed(sample_order, sample_baseline_policy):
    engine = PolicyEngine(sample_baseline_policy)

    decision = engine.evaluate(
        {"action": "cancel_order"},
        sample_order,
        {"fraud_flag": False}
    )

    assert decision["approved"] is True

def test_fraudulent_account_cancellation_not_llowed(sample_order, sample_user_flagged_policy):
    engine = PolicyEngine(sample_user_flagged_policy)

    decision = engine.evaluate(
        {"action": "cancel_order"}, 
        sample_order, 
        {"fraud_flag": True}
    )

    assert decision["approved"] is False     
