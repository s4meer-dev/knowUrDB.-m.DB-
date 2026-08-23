from pydantic import BaseModel, Field


class AIGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="The prompt to send to the AI")


class AIGenerateResponse(BaseModel):
    response: str
    model: str
    status: str


class AIStatusResponse(BaseModel):
    provider: str
    model: str
    configured: bool
    status: str
