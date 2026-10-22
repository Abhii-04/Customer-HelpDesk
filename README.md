# Laya Helpdesk

A fullstack customer-support demo with a browser chat, a FastAPI backend, and a Laya-powered agent. Python tools answer order-status questions, while DeepSeek generates answers from a supplied product catalog and return policy. FastAPI serves both the frontend and API with one startup command.

## Requirements

- Python 3.12 or newer and `uv`.
- Network access for dependency installation and Laya's first model download, plus sufficient memory to run the local model.
- A DeepSeek API key for product and return-policy questions.

## Quick start

From the project directory, install dependencies:

```bash
uv sync
```

For product and return-policy replies, create a local `.env` file:

```dotenv
DEEPSEEK_API_KEY=your_api_key_here
# Optional: choose model IDs available to your DeepSeek account.
# SMALL_LLM=your_product_model
# BIG_LLM=your_return_policy_model
```

Start the web application from the project root:

```bash
uv run uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000> and type a message. No separate frontend server or Node build is required. Laya loads its model on first inference, so the first response can take longer. Stop the server with Ctrl+C.

The web entry point is `backend/app.py`. The root `main.py` is an optional terminal interface; it is not used to start the web application.

## Usage

Example inputs:

```text
KH-1042
Where is order KH-1043?
What size is the terracotta planter?
Can I return order KH-1044?
I want to speak to a person.
```

A bare order ID is expanded into an order-status question before classification. IDs follow the format `KH-` plus four digits and are matched without regard to case.

Press Enter to send, or Shift+Enter to add a new line. Suggested questions fill the message box. New chat clears the visible conversation. Failed requests restore your message so you can retry.

Messages must contain non-whitespace text and be at most 4,000 characters long. Each message is an independent agent request: earlier messages are displayed in the browser but are not supplied as conversation memory. Refreshing the page clears the visible history.

## Optional terminal interface

For an interactive CLI instead of the browser:

```bash
uv run python main.py
```

The CLI requires Python's `readline` module for input history. Use the Up arrow to recall input; `quit`, `exit`, Ctrl+C, or Ctrl+D closes the session.

To process one request and exit:

```bash
uv run python main.py "Where is order KH-1042?"
```

## Configuration

Environment variables are loaded from `.env`; values already set in the environment take precedence. Local `.env` files are ignored by Git.

| Variable | Purpose | Default |
| --- | --- | --- |
| `DEEPSEEK_API_KEY` | Credential for product and return-policy replies | Unset |
| `SMALL_LLM` | DeepSeek model used for product questions | `deepseek-v4-pro` |
| `BIG_LLM` | DeepSeek model used for return-policy questions | `deepseek-v4-pro` |

The defaults are the values configured in this repository. Set the model variables to IDs available to your account. DeepSeek requests use `https://api.deepseek.com`.

Routing and reply-check thresholds live in `agent/config/config.py`:

| Setting | Default | Effect |
| --- | --- | --- |
| `MIN_INTENT_CONFIDENCE` | `0.5` | Ask for clarification below this confidence |
| `WANTS_HUMAN_CUTOFF` | `0.7` | Select the human route above this probability |
| `GUARD_HOLD_AT` | `0.75` | Reject generated replies at or above this probability of overpromising or inventing facts |
| `GUARD_MIN_ANSWERED` | `0.5` | Reject generated replies below this probability of answering the customer |

## Request flow

Browser → `POST /start-agent` → `classify` → `decide` → `handle` → check generated replies → JSON response → chat bubble

The browser submits form-encoded `user_input`. Successful responses contain a `response` string; `chat_id` and `user_id` currently default to `null` and do not provide sessions. Invalid input returns HTTP 422. Agent failures return HTTP 500 with a generic customer-facing message; details are logged on the server.

Laya classifies intent, complexity, and whether the customer wants a person. Route selection applies these rules in order:

| Condition | Route | Response source |
| --- | --- | --- |
| Customer wants a person above the cutoff | `human` | Fixed handoff message |
| Intent confidence is below the minimum, or intent is `other` | `clarify` | Fixed clarification message |
| Order-status question | `tool` | Python lookup of sample orders |
| Product question | `small_llm` | DeepSeek with the supplied catalog |
| Complaint | `human` | Fixed handoff message |
| Return or exchange question | `big_llm` | DeepSeek with the return policy and computed order facts |

Complexity is collected but does not independently select a route. Delivery-day calculations stay in Python, and the return window is seven days.

The web backend checks product and return-policy replies for unsupported promises, invented facts, and whether they answer the request. Rejected generated replies display `Reply needs human review.` Tool, clarification, and human replies are returned directly. The optional CLI checks every reply and checks generated replies a second time; only generated replies use the verdict to withhold a response.

## Project structure

```text
backend/app.py                     Web entry point, frontend serving, agent endpoint
backend/model.py                   API response model
frontend/templates/index.html      Chat page
frontend/static/chat.js            Chat interactions and API requests
frontend/static/styles.css         Responsive styling
tests/test_integration.py          Offline API integration tests
main.py                            Optional interactive and one-shot CLI
agent/config/config.py             Model settings, thresholds, shared Laya router
agent/config/signals.py            Signals, Route, and Verdict dataclasses
agent/config/catalog_and_policy.py Product catalog and return-policy text
agent/database/store.py            Sample orders and return-window setting
agent/tools/order_lookup.py        Order-ID extraction, lookup, delivery-day calculation
agent/nodes/router.py              Laya classification questions and validation
agent/nodes/classify.py            Async classification and route selection
agent/nodes/handlers.py            Route handlers, DeepSeek calls, reply verdicts
agent/nodes/response_checker.py    Laya reply checks and acceptance rules
```

## Demo limitations

Orders and catalog entries are in-memory sample data. Delivery dates are fixed demo values; days since delivery are calculated using the date captured when the store module loads, so return eligibility changes over time.

The human route announces a teammate handoff and a reply within two hours, but no handoff integration exists yet. The human-review fallback also does not create a review ticket.

## Tests and reports

Run the offline integration suite:

```bash
uv run python -m unittest discover -s tests -v
```

The suite covers frontend asset serving, order handling, input validation, generated-reply checks, and error responses. Inference is mocked for repeatability; it does not verify live Laya or DeepSeek availability.

See the [integration report](docs/INTEGRATION_REPORT.md) and [backend changes report](docs/BACKEND_CHANGES_REPORT.md) for verification results and follow-up suggestions.
