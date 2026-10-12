import asyncio
import sys
import readline

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from agent.nodes.classify import classify, decide
from agent.nodes.handlers import handle, check_reply
from agent.tools.order_lookup import find_order_id


async def main():
    console = Console()
    interactive = len(sys.argv) == 1
    if interactive:
        console.print(Panel(
            "[bold cyan]LAYA HELPDESK[/bold cyan]\n\n"
            "Enter an order ID or ask a support question.\n"
            "[dim]Example: KH-1042 · Up arrow recalls input · quit exits[/dim]",
            border_style="cyan",
            padding=(1, 2),
        ))
    while True:
        try:
            message = console.input("\n[bold cyan]You › [/bold cyan]").strip() if interactive else " ".join(sys.argv[1:]).strip()
        except EOFError:
            console.print("\n[dim]Goodbye![/dim]")
            return
        if interactive and message.lower() in {"quit", "exit"}:
            console.print("[dim]Goodbye![/dim]")
            return
        if not message:
            if interactive:
                continue
            return
        order_id = find_order_id(message)
        if order_id and message.upper() == order_id:
            message = f"What is the status of order {order_id}?"
        try:
            with console.status("[cyan]Laya is checking your request…[/cyan]", spinner="dots"):
                signals = await classify(message)
                route = decide(signals)
                reply, context, _ = await handle(route.name, message)
                verdict = await check_reply(message, reply, context)
            if route.name in {"small_llm","big_llm"}:
                verdict=await check_reply(message,reply,context)
                accepted=verdict.send
            else:
                accepted=True
            response = reply if accepted else "Reply needs human review."
            if interactive:
                console.print(Panel(Text(response), title="Laya", border_style="cyan" if verdict.send else "yellow", padding=(1, 2)))
            else:
                console.print(response, markup=False, highlight=False)
        except Exception as error:
            if not interactive:
                raise
            console.print("Could not complete this request. Please try again.", style="red")
            console.print(str(error), style="dim", markup=False, highlight=False)
        if not interactive:
            return


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nGoodbye!")
