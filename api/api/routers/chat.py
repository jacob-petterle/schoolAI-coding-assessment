from fastapi import APIRouter
from pydantic import BaseModel
from aws_lambda_powertools import Logger

from api.settings import Settings


SETTINGS = Settings()  # type: ignore - pulled from the environment
LOGGER = Logger(level=SETTINGS.log_level)

module_name = __name__.rsplit(".", maxsplit=1)[-1].replace("_", "-")
ROUTER = APIRouter(prefix=f"/{module_name}", tags=[module_name])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


@ROUTER.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    # For now, we'll just echo the message back
    return ChatResponse(response=f"You said: {request.message}")
