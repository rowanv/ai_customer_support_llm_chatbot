# ai_customer_support_agent
An agent that uses a customer-facing LLM chatbot to handle order-related actions (cancellations and tracking) by enforcing relevant policies.


### Setup

#### Virtual Env generation
```
python3 -m venv proj_ai_customer_support_agent
source proj_ai_customer_support_agent/bin/activate
pip install -r requirements.txt
```

#### Run tests
```bash
export PYTHONPATH=$PWD/src
pytest -q
```




# Architecture

- Note that we are assuming that the LLM call, policy evaluation, and API call all finish within a fairly short time period. If we had policies that required longer evaluation processes (such as running a risk model that could take 30+ seconds to complete) - we would want to further decouple the architecture to use a more fully asynchronous workflow.

## Policies
- Policies can be pulled via an API endpoint. This decouples the policies themselves from the codebase. Among other benefits, this means that the company's policies can be viewed by non-technical stakeholders via another interface, and tha t the policies themselves can be edited dynamically without needing to touch the agent codebase. 


```/api/v1/policies/
```

Sample response:
```
GET: {
  "policies": [
    {
      "id": "standard_cancellation_window",
      "type": "time_window",
      "max_days": 10,
      "priority": 3
    },
    {
      "id": "no_cancel_after_shipping",
      "type": "status_block",
      "blocked_statuses": ["shipped", "delivered"],
      "priority": 2
    },
    {
      "id": "high_value_identity_verification",
      "type": "value_threshold",
      "min_amount": 500,
      "requires_verification": true,
      "priority": 1
    },
    {
      "id": "fraud_flag_restriction",
      "type": "fraud_block",
      "block_actions": ["cancel_order"],
      "priority": 0
    }
  ]
}
```