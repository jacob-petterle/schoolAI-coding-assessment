from pathlib import Path
import os
from projen.python import PythonProject


AUTHORS = [
    "Jacob Petterle",
]
AUTHOR_EMAIL = "jacobpetterle@tai-tutor.team"
ROOT_PROJECT_NAME = "root-project"
IAC_PROJECT_NAME = "iac"
IAC_MODULE_NAME = IAC_PROJECT_NAME.replace("-", "_")
INDEXER_PROJECT_NAME = "indexer"
INDEXER_MODULE_NAME = INDEXER_PROJECT_NAME.replace("-", "_")
API_PROJECT_NAME = "api"
API_MODULE_NAME = API_PROJECT_NAME.replace("-", "_")
PYTHON_VERSION = "3.10"
PYTHON_DEP = f"python@^{PYTHON_VERSION}"
AWS_PROFILE_NAME = os.getenv("AWS_PROFILE", "default")

# Root Project
ROOT_PROJECT = PythonProject(
    author_email=AUTHOR_EMAIL,
    author_name=AUTHORS[0],
    module_name="",
    name=ROOT_PROJECT_NAME,
    version="0.0.0",
    poetry=True,
    pytest=False,
    deps=[
        PYTHON_DEP,
    ],
    dev_deps=[
        f"{IAC_MODULE_NAME}@{{path = './{IAC_PROJECT_NAME}', develop = true}}",
        f"{INDEXER_MODULE_NAME}@{{path = './{INDEXER_MODULE_NAME}', develop = true}}",
        f"{API_MODULE_NAME}@{{path = './{API_PROJECT_NAME}', develop = true}}",
    ],
)
ROOT_PROJECT.add_git_ignore("**/cdk.out")
ROOT_PROJECT.add_git_ignore("**/.venv*")

# IAC Project
IAC_PROJECT = PythonProject(
    parent=ROOT_PROJECT,
    author_email=AUTHOR_EMAIL,
    author_name=AUTHORS[0],
    module_name=IAC_MODULE_NAME,
    name=IAC_PROJECT_NAME,
    outdir=IAC_PROJECT_NAME,
    version="0.0.0",
    description="Infrastructure as Code for the RAG system",
    poetry=True,
    deps=[PYTHON_DEP, "aws-cdk-lib@^2.0.0", "aws-cdk.aws-lambda-python-alpha@^2.153.0a0"],
    dev_deps=[
        "pytest@^6.2.5",
    ],
)
DEPLOY_CMD = (
    f"export AWS_PROFILE={AWS_PROFILE_NAME} && npx cdk deploy "
    f"--app 'python app.py' --require-approval never --asset-parallelism "
    f"--asset-prebuild false --concurrency 5"
)
DEPLOY_CMD_NAME = "cdk-deploy"
IAC_PROJECT.add_task(
    DEPLOY_CMD_NAME,
    exec=DEPLOY_CMD,
    cwd=f"./{Path(IAC_PROJECT.outdir).name}",
    receive_args=True,
)
ROOT_PROJECT.add_task(
    DEPLOY_CMD_NAME,
    cwd=f"./{Path(IAC_PROJECT.outdir).name}",
    exec=DEPLOY_CMD,
    receive_args=True,
)


INDEXER_PROJECT = PythonProject(
    parent=ROOT_PROJECT,
    author_email=AUTHOR_EMAIL,
    author_name=AUTHORS[0],
    module_name=INDEXER_MODULE_NAME,
    name=INDEXER_PROJECT_NAME,
    outdir=INDEXER_PROJECT_NAME,
    version="0.0.0",
    description="Indexer for the documents",
    poetry=True,
    deps=[PYTHON_DEP, "aws-lambda-powertools@^2.43.1", "pydantic@^2.8.0", "pyarrow@^17.0.0", "boto3@^1.35.2", "pydantic-settings@^2.4.0"],
    dev_deps=[
        "pytest@^6.2.5",
        "requests@^2.26.0",
        "boto3-stubs@{version = '^1.34.105', extras = ['s3']}",
    ],
)


API_PROJECT = PythonProject(
    parent=ROOT_PROJECT,
    author_email=AUTHOR_EMAIL,
    author_name=AUTHORS[0],
    module_name=API_MODULE_NAME,
    name=API_PROJECT_NAME,
    outdir=API_PROJECT_NAME,
    version="0.0.0",
    description="API for the RAG system",
    poetry=True,
    deps=[PYTHON_DEP, "fastapi@^0.112.1", "pydantic@^2.8.0", "mangum@^0.17.0", "aws-lambda-powertools@^2.43.1"],
    dev_deps=[
        "pytest@^6.2.5",
    ],
)


# Synthesize all projects
API_PROJECT.synth()
INDEXER_PROJECT.synth()
IAC_PROJECT.synth()
ROOT_PROJECT.synth()
