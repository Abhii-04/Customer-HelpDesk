from pydantic import BaseModel


class AgentResponse(BaseModel):
    response: str
    chat_id: int | None = None
    user_id: str | None = None
