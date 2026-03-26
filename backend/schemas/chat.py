from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class ChatAction(BaseModel):
    tool: str
    summary: str


class ChatResponse(BaseModel):
    response: str
    actions_taken: list[ChatAction] = []
