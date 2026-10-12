# Changes made to Laya Helpdesk

This document explains the migration and connection work. All application functions already existed; their bodies, signatures and imports were corrected to make them work together. No additional application functions were created.

## 1. Connected the entrypoint to the full request flow

Previously, `main.py` only printed a greeting and `agent/agent.py` was empty. The existing `main()` now accepts a customer message and runs classification, route selection, the selected handler and the reply check.

```python
async def main():
    message = " ".join(sys.argv[1:]).strip() or input("Customer: ").strip()
    if not message:
        return
    signals = await classify(message)
    route = decide(signals)
    reply, context, _ = await handle(route.name, message)
    verdict = await check_reply(message, reply, context)
    print(reply if verdict.send else "Reply needs human review.")
```

**Why:** The individual functions needed a caller to connect them. The existing entrypoint provides that connection without introducing an agent framework or another orchestration function. It processes one message per run.

## 2. Replaced the remaining TypeSafe client calls with Laya

Some files already called Laya, but `classify()` still referenced an undefined `AsyncTypeSafeClient` and read attributes from a different response format. It now calls the existing router function, which uses Laya's dictionary response.

```python
# agent/nodes/router.py
prediction = laya_router.predict(message, question)
answers = prediction["answers"]
```

```python
# agent/nodes/classify.py
result = await asyncio.to_thread(router, message)
return Signals(
    intent=result["intent"],
    intent_confidence=result["intent_confidence"],
    complexity=result["complexity"],
    wants_human=result["wants_human"],
    ms=(time.perf_counter() - start) * 1000,
)
```

**Why:** Classification and checking must use the same installed Laya API. `asyncio.to_thread()` lets the existing asynchronous flow call synchronous Laya inference without running it directly on the event loop.

The router and checker now share the `Router()` instance in `agent/config/config.py`. Imports of the nonexistent `agent.config.state` were removed. The CLI passes the current message for classification and a dictionary of customer request, reply and facts for checking.

## 3. Aligned classification values with route selection

Laya's department choices use hyphens, while `decide()` previously compared underscore names. The comparisons now match the returned choices.

```python
if s.intent == "order-status":
    return Route("tool", "status is a database lookup, no LLM needed")
if s.intent == "product-question":
    return Route("small_llm", "catalog question, a small llm model is enough")
```

**Why:** A correctly classified order-status request otherwise fell through to the policy LLM route.

The `Signals.complexity` field changed from `float` to `str`, because the existing Laya question returns a choice such as `simple`, `needs judgement` or `messy`. Complaint reasons now display that choice without numeric formatting.

| Condition, in decision order | Route |
| --- | --- |
| Human-request probability exceeds the cutoff | `human` |
| Intent confidence is below the minimum | `clarify` |
| Intent is `other` | `clarify` |
| Intent is `order-status` | `tool` |
| Intent is `product-question` | `small_llm` |
| Intent is `complaint` | `human` |
| Remaining supported intent: `return-exchange` | `big_llm` |

The existing decision priorities were retained. Complexity is collected but does not independently select a route.

## 4. Repaired handler calls and return values

The handlers called missing functions on `store`, passed the wrong number of arguments to `ask_llm()`, and tried to unpack plain strings into `reply, context`. They now import the existing order tools and return the documented tuple consistently.

```python
from agent.tools.order_lookup import find_order_id, days_since_delivery, order_lookup
```

```python
elif route_name == "tool":
    reply = order_lookup(message)
    context = reply
elif route_name == "small_llm":
    context = CATALOG
    reply = await ask_llm(SMALL_LLM, PRODUCT_PROMPT, message)
```

**Why:** The tools already existed in `agent/tools/order_lookup.py`; the handlers needed to call them there. Every branch now supplies a reply and the context used by the checker. Unknown handler route names raise `ValueError` rather than silently invoking the policy model.

## 5. Made the existing DeepSeek function send and return the right data

Previously, `ask_llm()` ignored its arguments, sent only combined system prompts and returned nothing. The model client was also constructed during import. It now uses the requested model, sends both the system prompt and customer message, and returns the response content.

```python
async def ask_llm(mode: str, system: str, message: str) -> str:
    llm = ChatOpenAI(
        api_key=os.getenv('DEEPSEEK_API_KEY'),
        model=mode,
        base_url="https://api.deepseek.com",
    )
    response = await llm.ainvoke([
        SystemMessage(content=system),
        HumanMessage(content=message),
    ])
    return response.content
```

**Why:** Product and return handlers require the customer's actual question and a usable reply. Constructing the client inside the existing function also lets order lookup and imports work without a DeepSeek credential.

## 6. Corrected prompt construction and branding

The product and policy prompts referred to a perfume brand despite the home-goods catalog. They now refer to Laya Helpdesk. The original policy prompt evaluated `order_facts` before that function was defined. It now keeps placeholders until the return handler has computed the facts.

```python
POLICY_PROMPT = """You handle returns for Laya Helpdesk.
Follow the policy exactly. Never offer anything the policy does not allow.
Reply in 3-4 short sentences.
POLICY: {policy}
ORDER_FACTS: {facts}
"""
```

```python
facts = order_facts(message)
context = f"{RETURN_POLICY}\n{facts}"
prompt = POLICY_PROMPT.format(policy=RETURN_POLICY, facts=facts)
reply = await ask_llm(BIG_LLM, prompt, message)
```

**Why:** The prompt must match the supplied catalog, and order facts must be computed before being inserted. Return-window calculations remain in Python.

## 7. Connected the reply checker and rejection path

`check_reply()` previously used the old client API, an undefined `CHECKS` variable and a broken result iteration. It now delegates to the existing Laya `response_checker()` and builds the existing `Verdict` dataclass.

```python
state = {"customer": message, "reply": reply, "facts": allowed_facts or "(none)"}
result = await asyncio.to_thread(response_checker, state)
p = {name: answer["noul"] for name, answer in result["checks"].items()}
```

The acceptance conditions are:

```python
accepted = (
    answers["over_promises"]["noul"] < GUARD_HOLD_AT
    and answers["invent_facts"]["noul"] < GUARD_HOLD_AT
    and answers["answer_customer"]["noul"] >= GUARD_MIN_ANSWERED
)
```

**Why:** The draft needs checking against its allowed facts before being printed. Flags now use the same boundary as acceptance: a risk probability equal to `GUARD_HOLD_AT` is rejected and flagged. Existing probability and choice validation was retained.

A rejected draft produces `Reply needs human review.` It does not create a review ticket.

## 8. Fixed order-ID matching and malformed demo dates

The original regex used an `fr` string. Python treated `{4}` as interpolation, making the pattern match a literal digit `4` instead of four digits. The unnecessary `f` prefix was removed.

```python
ORDER_ID = re.compile(r"\bKH-\d{4}\b", re.IGNORECASE)
```

**Why:** Valid IDs such as `KH-1042` must match before any lookup or return calculation can work.

The store now uses the current date:

```python
TODAY = date.today()
```

Malformed dates were replaced with valid demo dates: the shipped order's ETA is `2026-10-25`, and delivered orders use `2026-10-08`. String `"None"` ETA values became Python `None`.

**Why:** Malformed delivery dates caused date parsing to fail. The replacement dates are sample values, not verified delivery records. The brass diya order/catalog price difference was left for confirmation and recorded in `SUGGESTIONS.md`.

## 9. Restored the human handoff message

At your request, the human handler again announces a teammate handoff and a reply within two hours:

```python
reply = "I am passing you to a teammate now. They will reply within 2 hours."
context = "The customer is being passed to a teammate, who will reply within 2 hours."
```

**Why:** You plan to integrate the human node. The matching context lets the existing reply checker evaluate this message against the intended handoff behavior. This restores the message and timing promise; the human-node integration itself is still pending.

## 10. Organized files and removed unused pieces

| Original file | Current file | Reason |
| --- | --- | --- |
| `agent/config/Signals.py` | `agent/config/signals.py` | Consistent lowercase module naming |
| `agent/nodes/typesafe_router.py` | `agent/nodes/router.py` | Name matches the Laya router implementation |
| `agent/nodes/typesage_response_Checker.py` | `agent/nodes/response_checker.py` | Removed legacy naming and typo |
| `agent/agent.py` | Removed | Empty placeholder; existing `main()` connects the flow |
| `agent/middleware/guard.py` | Removed | Empty placeholder; checking uses existing node functions |

Unused imports were removed from touched files. The empty middleware directory was removed. Small wording errors in the catalog, policy and checker instructions were corrected.

## 11. Simplified dependencies and environment configuration

The direct dependencies now reflect what the application uses:

```toml
dependencies = [
    "python-dotenv>=1.0.0",
    "langchain-openai>=1.7.0",
    "laya>=0.4.6",
]
```

**Why:** The umbrella `langchain` dependency was unused. Removing it also removed unused graph-related packages from `uv.lock`. The `dotenv` wrapper was replaced by the directly used `python-dotenv` package. `langchain-openai` remains for the existing DeepSeek client.

Environment loading no longer overrides already-set environment variables. The existing model defaults can now be overridden:

```python
load_dotenv()
router = Router()
SMALL_LLM = os.getenv('SMALL_LLM', 'deepseek-v4-pro')
BIG_LLM = os.getenv('BIG_LLM', 'deepseek-v4-pro')
```

Local `.env` files were added to `.gitignore`. The project description was updated, `README.md` gained setup and run instructions, and `SUGGESTIONS.md` records improvements that were not implemented.

## Verification and remaining limits

Dependency sync and Python compilation passed. Temporary checks covered all five CLI routes, decision precedence, order tools, checker boundaries, rejected replies and DeepSeek message forwarding using mocked inference/provider calls. No test functions were added to the repository.

A real run using the cached Laya model in offline mode returned:

```text
KH-1042 (jaipur block print bedsheet) is shipped with Delhivery expected by 2026-10-25
```

Live DeepSeek calls were not tested because `DEEPSEEK_API_KEY` was not configured. The cached Laya checkpoint emitted a temperature-clamping warning; calibration review is recorded in `SUGGESTIONS.md`. Human handoff, persistent conversations and a real order backend remain unimplemented suggestions.

To run the connected CLI:

```bash
uv sync
uv run python main.py "Where is order KH-1042?"
```

## 12. Added an interactive terminal session

This follow-up changes the earlier single-request behavior: running `uv run python main.py` without arguments now opens a persistent input loop inside the existing `main()` function. No new application functions were added.

Rich renders the welcome panel, processing spinner and reply panels. It is now a direct dependency. The standard-library `readline` module enables input editing and Up-arrow recall on this Linux environment.

A bare order ID becomes an explicit status question before classification:

```python
order_id = find_order_id(message)
if order_id and message.upper() == order_id:
    message = f"What is the status of order {order_id}?"
```

**Why:** Customers can enter `KH-1042` directly and keep checking orders without repeating the shell command. The existing classification, handler and reply-check flow still processes each request.

Blank input prompts again. `quit`, `exit`, Ctrl+D and Ctrl+C end the session. Request failures show an error and allow another input. Commands with a message argument still process one request and exit. Replies render as literal text so customer or model text cannot introduce Rich formatting.

Input-loop verification covered repeated requests, blank input, bare IDs, literal reply text, error recovery, withheld replies, EOF and one-shot behavior with mocked inference. Compilation and dependency sync passed. The loop does not introduce conversation memory.

A live offline session using the cached Laya model accepted `KH-1042`, ran the agent flow, displayed `Reply needs human review.` when the checker rejected the draft, and returned to the prompt before exiting on `quit`. The checkpoint again emitted its calibration warning. This verifies the interactive flow, not consistent model acceptance of order replies.
