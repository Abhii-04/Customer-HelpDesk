import os 
from dotenv import load_dotenv
from laya import Router

load_dotenv()

router=Router()

SMALL_LLM=os.getenv('SMALL_LLM', 'deepseek-v4-pro')
BIG_LLM=os.getenv('BIG_LLM', 'deepseek-v4-pro')
MIN_INTENT_CONFIDENCE=0.5   #below this , ask the customer to clarify
WANTS_HUMAN_CUTOFF=0.7  #complaints scored above this goes to a person
GUARD_HOLD_AT=0.75  #measured:honest replies 0.36-0.53,invented facts 0.8
GUARD_MIN_ANSWERED=0.5  #below this, the reply missed the customer question
