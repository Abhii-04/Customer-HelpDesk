import logging
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from agent.nodes.classify import classify, decide
from agent.nodes.handlers import check_reply, handle
from agent.tools.order_lookup import find_order_id
from backend.model import AgentResponse


app = FastAPI(title="HelpDesk")
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
templates = Jinja2Templates(directory=frontend_dir / "templates")
app.mount("/static", StaticFiles(directory=frontend_dir / "static"), name="static")


async def run_agent(user_input: str):
    message = user_input
    order_id = find_order_id(message)
    if order_id and message.upper() == order_id:
        message = f"What is the status of order {order_id}?"

    signals = await classify(message)
    route = decide(signals)
    reply, context, _ = await handle(route.name, message)

    if route.name in {"small_llm", "big_llm"}:
        verdict = await check_reply(message, reply, context)
        return reply if verdict.send else "Reply needs human review."
    return reply


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})


@app.post("/start-agent", response_model=AgentResponse)
async def input_task(
    user_input: Annotated[str, Form(min_length=1, max_length=4000)],
):
    user_input = user_input.strip()
    if not user_input:
        raise HTTPException(status_code=422, detail="Please enter a message.")
    try:
        response = await run_agent(user_input)
        return AgentResponse(response=response)
    except Exception as error:
        logging.getLogger(__name__).exception("Agent request failed")
        raise HTTPException(
            status_code=500,
            detail="Could not process your message. Please try again.",
        ) from error
