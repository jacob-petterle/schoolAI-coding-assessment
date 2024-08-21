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
MY_SERVICE_PROJECT_NAME = "my-service"
MY_SERVICE_MODULE_NAME = MY_SERVICE_PROJECT_NAME.replace("-", "_")
AWS_PROFILE_NAME = "tb-de-dev"
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
        f"{MY_SERVICE_MODULE_NAME}@{{path = './{MY_SERVICE_PROJECT_NAME}', develop = true}}",
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
    description="Infrastructure as Code for the project",
    poetry=True,
    deps=[
        PYTHON_DEP,
        "aws-cdk-lib@^2.0.0",
    ],
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

# My-Service Project
MY_SERVICE_PROJECT = PythonProject(
    parent=ROOT_PROJECT,
    author_email=AUTHOR_EMAIL,
    author_name=AUTHORS[0],
    module_name=MY_SERVICE_MODULE_NAME,
    name=MY_SERVICE_PROJECT_NAME,
    outdir=MY_SERVICE_PROJECT_NAME,
    version="0.0.0",
    description="My Service for the project",
    poetry=True,
    deps=[
        PYTHON_DEP,
        "fastapi@^0.68.0",
        "uvicorn@^0.15.0",
    ],
    dev_deps=[
        "pytest@^6.2.5",
        "requests@^2.26.0",
    ],
)

# Synthesize all projects
MY_SERVICE_PROJECT.synth()
IAC_PROJECT.synth()
ROOT_PROJECT.synth()
