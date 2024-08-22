from textwrap import dedent
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools import Logger
from fastapi import APIRouter, FastAPI
from mangum import Mangum

from api.settings import Settings
from api.routers.documents import ROUTER as DOCUMENTS_ROUTER
from api.routers.retrieval import ROUTER as RETRIEVAL_ROUTER
from api.routers.chat import ROUTER as CHAT_ROUTER


SETTINGS = Settings()
LOGGER = Logger(level=SETTINGS.log_level)


ROUTER = APIRouter(prefix="/health-check", tags=["health-check"])


@ROUTER.get("/")
def health_check():
    return {"status": "ok"}


ROUTERS = [
    ROUTER,
    DOCUMENTS_ROUTER,
    RETRIEVAL_ROUTER,
    CHAT_ROUTER,
]


def create_app():
    """Create the FastAPI app."""
    settings = Settings()  # type: ignore - pulled from the environment
    LOGGER.debug("Creating FastAPI app", body=settings)

    app = FastAPI(
        title="SchoolAI RAG coding challenge",
        description=dedent("""
        # SchoolAI RAG System

        This API provides a Retrieval-Augmented Generation (RAG) system for question answering.

        ## How to Use the System

        1. **Add documents**
            - Use the `POST /documents` endpoint to upload files from the [SciQ dataset](https://allenai.org/data/sciq).
            - Recommendation: Keep individual resource files to less than 2000 rows to minimize indexing time.
            - Note: Indexing for a 1000 line file takes about 1 minute.

        2. **Check indexing status**
            - Use the `GET /documents/{resource_id}` endpoint to check the indexing status of a document.

        3. **Query documents**
            - Use the `POST /retrieval/query` endpoint to find relevant documents for a given query.

        4. **Chat**
            - Use the `POST /chat/chat` endpoint to ask questions and get AI-generated responses.

        5. **Delete documents**
            - Use the `DELETE /documents/{resource_id}` endpoint to remove resources you no longer need.

        ## Example Question

        > "What percentage of earth is covered in water?"

        ## Important Notes

        - This system only works with the SciQ dataset. Ensure your uploaded documents are from this dataset for optimal performance.
        - Indexing time varies based on document size. Be patient after uploading large documents.
        - You can delete resources that are no longer needed to manage your dataset.

        For more details on each endpoint, refer to the specific endpoint documentation below.
        """
        ),
        version="0.0.0",
    )

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
