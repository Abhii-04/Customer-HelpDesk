import math

from agent.config.config import router, GUARD_HOLD_AT, GUARD_MIN_ANSWERED

checks={
    "over_promises":{
        "type":"noul",
        "instructions":"Does the reply promise anything that the allowed facts do not permit?",
    },
    "invent_facts":{
        "type":"noul",
        "instructions":"Does the reply invent facts unsupported by the allowed facts?",
    },
    "answer_customer":{
        "type":"noul",
        "instructions":"Does the reply address the customer request?",
    }
}
def response_checker(state: dict):
    res_checker = router.predict(state, checks)
    answers=res_checker["answers"]
    for name in checks:
        value=answers[name]["noul"]
        if not isinstance(value,(int,float)) or not math.isfinite(value) or not 0<=value<=1:
            raise ValueError("Invalid checker probability")
    accepted=(answers["over_promises"]["noul"]<GUARD_HOLD_AT
              and answers["invent_facts"]["noul"]<GUARD_HOLD_AT
              and answers["answer_customer"]["noul"]>=GUARD_MIN_ANSWERED)
    return {"checks": answers, "accepted": accepted}
