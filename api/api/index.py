from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools import Logger
from fastapi import APIRouter, FastAPI
from mangum import Mangum

from api.settings import Settings

SETTINGS = Settings()
LOGGER = Logger(level=SETTINGS.log_level)


ROUTER = APIRouter(prefix="/health-check", tags=["health-check"])


@ROUTER.get("/health-check")
def health_check():
    return {"status": "ok"}


ROUTERS = [
    ROUTER,
]


def create_app():
    """Create the FastAPI app."""
    settings = Settings()  # type: ignore - pulled from the environment
    LOGGER.debug("Creating FastAPI app", body=settings)

    # Create app
    app = FastAPI(
        title="SchoolAI RAG coding challenge",
        description="API for the RAG system",
        version="0.0.0",
    )

    # Add routers
    for router in ROUTERS:
        app.include_router(router)

    return app


@LOGGER.inject_lambda_context(log_event=True)
def handler(event, context: LambdaContext):
    try:
        app = Mangum(create_app())
        LOGGER.debug("Invoking FastAPI app", body={"event": event})
        response = app(event, context)  # type: ignore - the context is using a Mangum type instead of power tools type
    except Exception as e:
        LOGGER.error("An error occurred", body={"error": e, "event": event})
        raise
    return response
