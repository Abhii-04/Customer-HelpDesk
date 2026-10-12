""" The existing store backend: orders,catalog,return policy and two plain tools.

Inputs: a customer message (for order-ID extraction)
Outputs: order facts and computed numbers.No AI anywhere in this file .
"""

from datetime import date

TODAY=date.today()
RETURN_WINDOW_DAYS=7

ORDERS:dict[str,dict]={
    "KH-1042":{
        "item":"jaipur block print bedsheet",
        "price":1499,
        "status":"shipped",
        "courier":"Delhivery",
        "eta":"2026-10-25",
        "delivered_on":None
    },

    "KH-1043": {
        "item":"brass diya set",
        "price":499,
        "status":"delivered",
        "courier":"Blue dart",
        "eta":None,
        "delivered_on":"2026-10-08"
    },
    "KH-1044": {
        "item":"Handloom cotton saree",
        "price":3299,
        "status":"delivered",
        "courier":"Ekart",
        "eta":None,
        "delivered_on":"2026-10-08"
    }
}

