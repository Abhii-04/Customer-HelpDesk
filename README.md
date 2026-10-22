# Laya Helpdesk

A command-line customer-support demo that uses local Laya inference to classify requests and check replies. Python tools answer order-status questions, while DeepSeek generates answers from a supplied product catalog and return policy.

## Requirements

- Python 3.12 or newer and `uv`.
- A terminal with support for Python's `readline` module (the CLI uses it for input history).
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

Then start the interactive terminal:

```bash
uv run python main.py
```

Enter an order ID such as `KH-1042` or a support question at the `You ›` prompt. The terminal displays a welcome panel, a processing spinner, and boxed replies. Laya downloads its model on first inference, so the first request can take longer.

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

Use the Up arrow to recall earlier input. Blank input prompts again; `quit`, `exit`, Ctrl+C, or Ctrl+D closes the session. If a request fails, the interactive terminal displays the error and lets you try another request. Each request is independent; input history does not provide conversation memory.

To process one request and exit, pass the message as an argument:

```bash
uv run python main.py "Where is order KH-1042?"
uv run python main.py "What size is the terracotta planter?"
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

`classify` → `decide` → `handle` → `check_reply` → display the response

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

Laya checks replies for unsupported promises, invented facts, and whether they answer the request. The current CLI checks every reply and checks generated replies a second time. Only the product and return-policy routes use the verdict to withhold a reply; tool, clarification, and human replies are displayed after the check completes. A rejected generated reply displays `Reply needs human review.`

## Project structure

```text
main.py                            Interactive and one-shot CLI
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

## Web chat

Run the full application from the project root:

```bash
uv sync
uv run uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000>. FastAPI serves the frontend and receives messages on the same origin; no separate frontend server or Node build is needed. Enter sends a message, Shift+Enter adds a line, and New chat clears the visible conversation. Messages are independent requests; the display is not agent memory and is cleared on refresh.

The browser submits URL-encoded `user_input` to `POST /start-agent`, which returns a JSON `response`. Messages must contain non-whitespace text and at most 4,000 characters. The existing Laya and DeepSeek requirements above still apply; initial Laya inference can take longer while its model loads. No credentials belong in the frontend.

Run the offline integration suite:

```bash
uv run python -m unittest discover -s tests -v
```

See [integration report](docs/INTEGRATION_REPORT.md) and [backend changes report](docs/BACKEND_CHANGES_REPORT.md) for verification results and follow-up suggestions.
