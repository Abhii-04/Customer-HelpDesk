from agent.config.config import router as laya_router
import math


question = {
    "department": {
        "type":"choice",
        "instructions":"What is the customer main reason for writing ?",
        "criteria": {
            "order-status":"",
            "product-question":"",
            "return-exchange":"",
            "complaint":"",
            "other":"",
        },
    },
    "complexity":{
        "type":"choice",
        "instructions":"How hard is it to solve this request?",
        "criteria":{
            "simple":"routine lookup",
            "needs judgement":"reasoning or policy interpretation",
            "messy":"dispute or exception requiring a human",
        },
    },
    "wants_human":{
        "type":"noul",
        "instructions":"Is customer asking to speak to a human?"
    }

}
def router(message: str):

    prediction = laya_router.predict(message, question)
    answers=prediction["answers"]
    values=[answers["department"]["answer_confidence"],
        answers["complexity"]["answer_confidence"],
        answers["wants_human"]["noul"]]
    for value in values:
        if not isinstance(value,(int,float)) or not math.isfinite(value) or not 0<=value<=1:
            raise ValueError("Invalid Laya probability")
    if answers["department"]["choice"] not in question["department"]["criteria"]:
        raise ValueError("Unknown department")
    if answers["complexity"]["choice"] not in question["complexity"]["criteria"]:
        raise ValueError("Unknown complexity")
    return {
        "intent":answers["department"]["choice"],
        "intent_confidence":answers["department"]["answer_confidence"],
        "complexity":answers["complexity"]["choice"],
        "complexity_confidence":answers["complexity"]["answer_confidence"],
        "wants_human":answers["wants_human"]["noul"],
    }
