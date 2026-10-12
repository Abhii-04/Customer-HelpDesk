# Laya Helpdesk

A command-line helpdesk using Laya for classification and reply checks, Python tools for order status, and DeepSeek for catalog and return-policy replies.

## Run

```bash
uv sync
uv run python main.py
```

Launch once, then type an order ID such as `KH-1042` or a support question at the `You ›` prompt. The terminal stays open for more requests. Use the Up arrow to recall previous input and type `quit` or `exit` to leave; Ctrl+C and Ctrl+D also exit.

The terminal shows a welcome panel, a processing spinner and boxed replies. A bare order ID is expanded into an order-status question before it goes through the existing agent flow. Each request is independent; the loop does not add conversation memory.

One-shot commands still work:

```bash
uv run python main.py "Where is order KH-1042?"
```

Product and return routes require `DEEPSEEK_API_KEY` in your environment or a local `.env` file. Set `SMALL_LLM` and `BIG_LLM` to the DeepSeek models available to your account; both currently default to the existing `deepseek-v4-pro` setting. Laya runs locally and downloads its model on first inference, requiring network access and sufficient memory.

Flow: `classify` → `decide` → `handle` → `check_reply` → print the accepted reply or `Reply needs human review.`

- `agent/config/`: thresholds, model names, dataclasses, catalog and policy.
- `agent/database/store.py`: sample orders and return window.
- `agent/tools/order_lookup.py`: order ID extraction, status lookup and delivery-day calculation.
- `agent/nodes/`: Laya routing/checking and existing handler functions.

The order records are demo data. The human route announces a teammate handoff and a reply within two hours. The human node still needs to be integrated to perform that handoff.
