from pydantic import BaseModel, EmailStr, Field


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None
    user_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    model: str = ""
    provider: str = ""
    cached: bool = False


class ConversationMessage(BaseModel):
    role: str
    content: str


class Conversation(BaseModel):
    id: str
    messages: list[ConversationMessage]
    created_at: float
    updated_at: float


class SummaryRequest(BaseModel):
    conversation_id: str
    custom_prompt: str | None = None
    user_id: str | None = None


class SummaryResponse(BaseModel):
    summary: str
    conversation_id: str
    model: str = ""
    provider: str = ""


class EmailRequest(BaseModel):
    to: EmailStr
    subject: str
    body: str
    conversation_id: str | None = None


class EmailResponse(BaseModel):
    sent: bool
    message_id: str = ""
