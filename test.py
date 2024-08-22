import pinecone
from aws_lambda_powertools.utilities.parameters import get_secret



index = pinecone.Index(
    api_key="737e4430-844a-44fa-b920-b963137fa117",
    host="https://ragstack-index0-d41d8cd98f00b204e980-c6xn8rd.svc.apw5-4e34-81fa.pinecone.io",
)
index.delete(delete_all=True)
