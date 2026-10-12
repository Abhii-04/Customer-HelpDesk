import asyncio
import time

from agent.config.signals import Signals, Route
from agent.config.config import MIN_INTENT_CONFIDENCE, WANTS_HUMAN_CUTOFF
from agent.nodes.router import router


async def classify(message: str) -> Signals:
    """Ask Laya all three questions about the message in a single call."""
    start = time.perf_counter()
    result = await asyncio.to_thread(router, message)
    return Signals(
        intent=result["intent"],
        intent_confidence=result["intent_confidence"],
        complexity=result["complexity"],
        wants_human=result["wants_human"],
        ms=(time.perf_counter() - start) * 1000,
    )


def decide(s:Signals)->Route:
    """Turn laya answer into a route.Ordinary if-statements,readable by anyone."""
    if s.wants_human > WANTS_HUMAN_CUTOFF:
        return Route("human",f"asked for a person ({s.wants_human:.2f})")
    
    if s.intent_confidence <MIN_INTENT_CONFIDENCE:
        return Route("clarify",f"not sure of the intent ({s.intent}@{s.intent_confidence:.2f})")
    
    if s.intent=="other":
        return Route("clarify","not a request the desk handles yet")
    
    if s.intent=="order-status":
        return Route("tool","status is a database lookup, no LLM needed")
    if s.intent=="product-question":
        return Route("small_llm","catalog question, a small llm model is enough")
    if s.intent == "complaint":
        return Route("human",f"messy complaint (complexity {s.complexity})")
    return Route("big_llm",f"{s.intent} needs policy judgement")

