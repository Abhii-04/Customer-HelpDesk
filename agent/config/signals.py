from dataclasses import dataclass


@dataclass
class Signals:
    """Laya answers about one message,plus how long the call took."""
    intent : str
    intent_confidence : float
    complexity: str
    wants_human:float
    ms: float

@dataclass
class Route:
    """where a message goes, and the reason in plain words."""
    name:str # "clarify"|"human"|"tool"|"small_llm"|"big_llm"
    reason:str

@dataclass
class Verdict:
    """Whether a reply can go out, and which checks fired."""
    send:bool
    flags:dict[str,float]
    ms:float