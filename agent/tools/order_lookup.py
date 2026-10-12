import re
from datetime import date

from agent.database.store import ORDERS, TODAY

ORDER_ID=re.compile(r"\bKH-\d{4}\b",re.IGNORECASE)

def find_order_id(message:str)->str|None:
    """pull the first order ID(like KH-1042) out of a message or None."""
    match = ORDER_ID.search(message)
    return match.group(0).upper() if match else None

def order_lookup(message:str)->str:
    """Answer an order status question straight from the database."""
    order_id=find_order_id(message)
    if order_id is None:
        return "please share your order ID (it looks like KH-1234) and I`ll check it."
    order = ORDERS.get(order_id)
    if order is None:
        return f"I could not find order {order_id}.Please double check the ID."
    if order["status"] =="delivered":
        return f"{order_id} {order["item"]} was delivered on {order["delivered_on"]}"
    return f"{order_id} ({order["item"]}) is {order["status"]} with {order["courier"]} expected by {order["eta"]}"

def days_since_delivery(order_id:str|None)->int|None:
    """Days between delivery and today.Date match lives in code,never in a model."""
    order=ORDERS.get(order_id or " ")
    if order is None or order["delivered_on"] is None:
        return None
    return (TODAY - date.fromisoformat(order["delivered_on"])).days
    
