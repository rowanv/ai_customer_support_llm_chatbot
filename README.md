# ai_customer_support_agent
An agent that uses a customer-facing LLM chatbot to handle order-related actions (cancellations and tracking) by enforcing relevant policies.


### Setup

#### Virtual Env generation
```
python3 -m venv proj_ai_customer_support_agent
source proj_ai_customer_support_agent/bin/activate
pip install -r requirements.txt
```

### Setting your OpenAI API key

You can set your OpenAI API key in your environment variables by running the following command in your terminal:

```bash
export OPENAI_API_KEY=your_api_key
```

You can also follow [these instructions](https://platform.openai.com/docs/libraries#create-and-export-an-api-key) to set your OpenAI key at a global level.


#### Run tests
```bash
pytest -q
```

### Running the server (development)

Recommended developer workflow:

1. Install package in editable mode (so `python_backend` is importable):

```bash
.venv/bin/python -m pip install -e .
```

2. Start the FastAPI app from the repository root (run as a module so package imports resolve):

```bash
.venv/bin/python -m uvicorn python_backend.main:app --reload --port 8000
```

Notes:
- If you prefer not to install editable, set `PYTHONPATH=$PWD/src` for test runs where `src/` is used.






# Architecture

- Note that we are assuming that the LLM call, policy evaluation, and API call all finish within a fairly short time period. If we had policies that required longer evaluation processes (such as running a risk model that could take 30+ seconds to complete) - we would want to further decouple the architecture to use a more fully asynchronous workflow.

## Local testing mode
This repository includes a small local HTTP API used for development and
component testing. The local API mimics external providers so the backend and
agents can be exercised fully offline.

### Server endpoints


#### Endpoints - ChatKit

- GET `/health`
  - Returns: 200 JSON `{ "status": "healthy" }`

- POST `/chatkit`
  - Internal endpoint used by the ChatKit runner. The body is forwarded into
    the `CustomerServiceServer.process` implementation and the endpoint will
    return either a streaming `text/event-stream` response or JSON depending
    on the server's return value.


#### Endpoints - Local API for Development 

Module: `python_backend/server_local_dev_api.py`

The local API registers routes with the FastAPI app when running locally
(`register_local_external_api(app)`). In production the application would call
the real external `/api/v1/...` endpoints instead of this module.


- GET `/api/v1/orders/{order_id}/`
  - Local stand-in for the external orders API. Used by agents and tests to
    resolve order ownership and shipment status.
  - Required header: `X-Customer-Email` (customer's email used to validate
    ownership).
  - Responses:
    - 200: order record JSON containing `order_id`, `customer_email`,
      `tracking_status`, `datetime_placed`, and `shipments` (each shipment has
      `carrier`, `tracking_number`, `status`, `estimated_delivery`).
    - 400: missing `X-Customer-Email` header
    - 403: header email does not match order owner
    - 404: order not found

Security & dev notes

- The local dev API stores data in-memory (`ORDERS_DB`) and is intended only
  for development/testing. It does not substitute for production integration
  with the real external provider.
- In production, ownership should be validated with authenticated identity
  rather than an arbitrary header. Avoid logging PII such as plaintext
  customer emails in production logs.
- Base CI integration included under `.github/workflows/`

### Testing the LLM chatbot

You can test the LLM chatbot locally using the sample email and order id included
with the local dev API. Example test values:

- Email: `a123@gmail.com`
- Order ID: `A123`

You can provide the information using the LLM frontend.


## Key pending items:

- Ensuring sufficient auth: The app does not currently engage in secure identity verification for cancellation operations. Implementation would depend on building out a more fully-featured authentication system, and then limiting actions that the user should not have access to.
- A more robust policy-handling system and architecture. Ideally, an external API that can be used to pull dynamically changing policy information. By creating an external microservice, this would also enable non-technical stakeholders to change policies in real-time. 
- Additional guardrails and data leakage management, including limiting the data that is passed directly to the LLM, where necessary. This would depend on company PII and usage requirements

## Additional items that would strengthen the app
- More robust secret management - while not hardcoded, many other ways to handle vs. a manually set environmental variable
- Adding telemetry and structured logs
- I'm not very satisfied with the way that the tests handle mocking/patching the Open AI dependencies. I'd ideally prefer to build out an external library along the lines of `getmoto/moto` for the `boto3` AWS client, which enables much cleaner testing. 
