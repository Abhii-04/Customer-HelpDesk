import asyncio
import os
import time

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from agent.config.signals import Verdict
from agent.config.catalog_and_policy import CATALOG, RETURN_POLICY
from agent.config.config import BIG_LLM, GUARD_HOLD_AT, GUARD_MIN_ANSWERED, SMALL_LLM
from agent.database import store
from agent.tools.order_lookup import find_order_id, days_since_delivery, order_lookup
from agent.nodes.response_checker import response_checker

PRODUCT_PROMPT = f"""You answer product questions for Laya Helpdesk.
Use only this catalog. If the answer is not in it, say you will check with the team.
Reply in 2-3 short sentences.

CATALOG: {CATALOG}
"""

POLICY_PROMPT = """You handle returns for Laya Helpdesk.
Follow the policy exactly. Never offer anything the policy does not allow.
Reply in 3-4 short sentences.
POLICY: {policy}
ORDER_FACTS: {facts}
"""


def order_facts(message: str) -> str:
    """Build the order facts the LLM may use; compute the day count here."""
    order_id = find_order_id(message)
    order = store.ORDERS.get(order_id)
    if order is None:
        return "No matching order found. Ask for a valid order ID."
    days = days_since_delivery(order_id)
    if days is None:
        return f"{order_id}: {order['item']}, Rs {order['price']}, not delivered yet."
    window = "inside" if days <= store.RETURN_WINDOW_DAYS else "outside"
    return (f"{order_id}: {order['item']}, Rs {order['price']}, delivered {days} days ago, "
            f"{window} the {store.RETURN_WINDOW_DAYS}-day return window.")


async def ask_llm(mode: str, system: str, message: str) -> str:
    """One chat call to DeepSeek with a system prompt and customer message."""
    llm = ChatOpenAI(
        api_key=os.getenv('DEEPSEEK_API_KEY'),
        model=mode,
        base_url="https://api.deepseek.com",
    )
    response = await llm.ainvoke([SystemMessage(content=system), HumanMessage(content=message)])
    return response.content


async def handle(route_name: str, message: str) -> tuple[str, str, float]:
    """Run the handler for a route; return reply, allowed facts, and elapsed ms."""
    start = time.perf_counter()
    if route_name == "clarify":
        reply = "Could you tell me a bit more? An order ID helps too."
        context = "Ask the customer to clarify their request and provide an order ID."
    elif route_name == "human":
        reply = "I am passing you to a teammate now. They will reply within 2 hours."
        context = "The customer is being passed to a teammate, who will reply within 2 hours."
    elif route_name == "tool":
        reply = order_lookup(message)
        context = reply
    elif route_name == "small_llm":
        context = CATALOG
        reply = await ask_llm(SMALL_LLM, PRODUCT_PROMPT, message)
    elif route_name == "big_llm":
        facts = order_facts(message)
        context = f"{RETURN_POLICY}\n{facts}"
        prompt = POLICY_PROMPT.format(policy=RETURN_POLICY, facts=facts)
        reply = await ask_llm(BIG_LLM, prompt, message)
    else:
        raise ValueError(f"Unknown route: {route_name}")
    return reply, context, (time.perf_counter() - start) * 1000


async def check_reply(message: str, reply: str, allowed_facts: str) -> Verdict:
    """Ask Laya three yes/no questions about the draft reply in one call."""
    state = {"customer": message, "reply": reply, "facts": allowed_facts or "(none)"}
    start = time.perf_counter()
    result = await asyncio.to_thread(response_checker, state)
    p = {name: answer["noul"] for name, answer in result["checks"].items()}
    fired = {name: p[name] for name in ("over_promises", "invent_facts") if p[name] >= GUARD_HOLD_AT}
    if p["answer_customer"] < GUARD_MIN_ANSWERED:
        fired["answer_customer"] = p["answer_customer"]
    return Verdict(send=result["accepted"], flags=fired, ms=(time.perf_counter() - start) * 1000)
