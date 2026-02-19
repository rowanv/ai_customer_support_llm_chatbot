# ai_customer_support_llm_chatbot
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

# Architecture

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
      `status`, `datetime_placed`, and `shipments` (each shipment has
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

- Email: `b456@gmail.com`
- Order ID: `B456`

You can provide the information using the LLM frontend.


## Architecture & Repo Structure (high-level)

This section gives a quick map of the main components and where to find them in the repository.

- `python_backend/` — core backend implementation
  - `main.py` : FastAPI app and registration of local dev API
  - `server.py` : ChatKit server implementation that orchestrates agents and threads
  - `server_local_dev_api.py` : in-memory local orders API used for development/tests
  - `customer_service/` : agent implementations and business logic
    - `customer_service_agents.py` : agent definitions, tools (`get_order_info`, `cancel_order_or_enforce_policies`)
    - `guardrail_agents.py` : lightweight guardrail functions used as input guardrails
  - `services/` : shared clients and schemas
    - `schemas.py` : Pydantic models for orders and standardized responses

- `tests/` — automated tests
  - `tests/test_server.py` : server-level tests
  - `tests/test_local_dev_api/` : tests for the local orders API
  - `tests/conftest.py` : test fixtures and fakes (note: prefer scoped fixtures / monkeypatch over global import mutation)

- `docs/` — experiment and evaluation notes (`docs/experimentation.md`)

- Tooling and config
  - `pyproject.toml`, `mypy.ini`, `.pre-commit-config.yaml` : linting/typecheck and pre-commit setup
  - `.github/workflows/` : CI workflow that runs tests and checks

Design notes:
- The architecture separates agent logic from the local external API to make it easy to run everything locally for development and testing.
- Agents are defined as small, composable tools so policy checks and external API calls are explicit and testable.
- For productionization you would replace the local orders API with a real external client and add authentication, structured logging, and metrics.


## Key pending items:

- Ensuring sufficient auth: The app does not currently engage in secure identity verification for cancellation operations. Implementation would depend on building out a more fully-featured authentication system, and then limiting actions that the user should not have access to.
- A more robust policy-handling system and architecture. Ideally, an external API that can be used to pull dynamically changing policy information. By creating an external microservice, this would also enable non-technical stakeholders to change policies in real-time. 
- Additional guardrails and data leakage management, including limiting the data that is passed directly to the LLM, where necessary. This would depend on company PII and usage requirements

## Additional items that would strengthen the app
- More robust secret management - while not hardcoded, many other ways to handle vs. a manually set environmental variable
- Adding telemetry and structured logs
- I'm not very satisfied with the way that the tests handle mocking/patching the Open AI dependencies. I'd ideally prefer to build out an external library along the lines of `getmoto/moto` for the `boto3` AWS client, which enables much cleaner testing. 