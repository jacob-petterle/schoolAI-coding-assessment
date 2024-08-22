import json
from pathlib import Path
from typing import Dict, Set, Tuple, Union, Optional, List
from constructs import Construct
from dataclasses import dataclass

import aws_cdk.aws_lambda as _lambda
import aws_cdk.aws_s3 as s3
import aws_cdk.aws_s3_notifications as s3n
import aws_cdk.aws_sqs as sqs
import aws_cdk.aws_logs as logs
import aws_cdk.aws_iam as iam
import aws_cdk.aws_lambda_event_sources as lambda_events
import aws_cdk.aws_secretsmanager as secretsmanager
import aws_cdk.aws_lambda_python_alpha as lambda_alpha
from aws_cdk import RemovalPolicy, Stack, Duration, Size, CfnOutput, SecretValue
from pydantic_settings import BaseSettings
from pinecone_db_construct import (
    PineconeIndex,
    CloudProvider,
    Region,
    PineconeIndexSettings,
    ServerlessSpec,
    DeploymentSettings,
)


from indexer.settings import Settings as IndexerSettings
from api.settings import Settings as ApiSettings


@dataclass
class FunctionUrlConfig:
    """Function URL configuration."""

    auth_type: Optional[_lambda.FunctionUrlAuthType] = None
    invoke_mode: Optional[_lambda.InvokeMode] = None


@dataclass
class LambdaConfig:
    """Lambda function configuration."""

    construct_id: str
    description: str
    index_directory: Union[str, Path]
    index_module_path: str = "function/index.py"
    handler: str = "handler"
    environment: Optional[BaseSettings] = None
    memory_size_mb: int = 256
    timeout: Duration = Duration.seconds(30)
    ephemeral_storage_size_mb: int = 512
    xray_tracing: _lambda.Tracing = _lambda.Tracing.DISABLED
    secret_names_to_read: Optional[List[str]] = None
    function_url_config: Optional[FunctionUrlConfig] = None


def model_dump_runtime_settings(
    settings: BaseSettings,
    *,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    round_trip: bool = False,
    warnings: bool = True,
    exclude: Optional[Set[str]] = None,
) -> Dict[str, str]:
    """Dump the settings model as a serialized python dict."""
    model_dict = settings.model_dump(
        mode="json",
        exclude=exclude,
        exclude_unset=exclude_unset,
        exclude_defaults=exclude_defaults,
        exclude_none=True,
        round_trip=round_trip,
        warnings=warnings,
    )
    output_dict = {}
    for key, value in model_dict.items():
        key = key.upper()
        if isinstance(value, str):
            output_dict[key] = value
        else:
            output_dict[key] = json.dumps(value)
    return output_dict


class RAGStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        bucket = s3.Bucket(
            self,
            "RAGBucket",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        queue = sqs.Queue(
            self,
            "RAGQueue",
            visibility_timeout=Duration.seconds(120),
        )

        bucket.add_event_notification(s3.EventType.OBJECT_CREATED, s3n.SqsDestination(queue))  # type: ignore
        bucket.add_event_notification(s3.EventType.OBJECT_REMOVED_DELETE, s3n.SqsDestination(queue))  # type: ignore

        secret = secretsmanager.Secret(
            self,
            "PineconeDBSecret",
            secret_string_value=SecretValue.unsafe_plain_text("737e4430-844a-44fa-b920-b963137fa117"),
        )

        lambda_config = LambdaConfig(
            construct_id="RAGLambda",
            description="Index documents from S3 bucket",
            index_directory="../indexer",
            index_module_path="indexer/index.py",
            timeout=Duration.seconds(60),
            memory_size_mb=512,
            environment=IndexerSettings(
                s3_bucket_name=bucket.bucket_name,
                pinecone_api_key_secret_name=secret.secret_name,
            ),
        )

        lambda_function, _ = self._get_lambda(lambda_config)
        lambda_function.add_to_role_policy(
            statement=iam.PolicyStatement(
                actions=["bedrock:InvokeModel"],
                resources=["*"],
            )
        )
        lambda_function.add_event_source(
            lambda_events.SqsEventSource(
                queue,
                batch_size=3,
                max_batching_window=Duration.seconds(5),
                max_concurrency=2,
            )
        )
        bucket.grant_read(lambda_function)

        api_lambda_config = LambdaConfig(
            construct_id="RAGApiLambda",
            description="API for interface for RAG system",
            index_directory="../api",
            index_module_path="api/index.py",
            timeout=Duration.seconds(30),
            memory_size_mb=256,
            function_url_config=FunctionUrlConfig(
                auth_type=_lambda.FunctionUrlAuthType.NONE,
                invoke_mode=_lambda.InvokeMode.BUFFERED,
            ),
            environment=ApiSettings(
                s3_bucket_name=bucket.bucket_name,
                pinecone_api_key_secret_name=secret.secret_name,
            ),
        )
        api_lambda, function_url = self._get_lambda(api_lambda_config)
        bucket.grant_read_write(api_lambda)
        CfnOutput(self, "ApiUrl", value=function_url.url)

        PineconeIndex(
            self,
            "PineconeIndex",
            index_settings=[
                PineconeIndexSettings(
                    api_key_secret_name=secret.secret_name,  # store as a string in secrets manager, NOT a key/value secret
                    dimension=1536,
                    removal_policy=RemovalPolicy.DESTROY,
                    pod_spec=ServerlessSpec(
                        cloud_provider=CloudProvider.AWS,
                        region=Region.US_WEST_2,
                    ),
                ),
            ],
            deployment_settings=DeploymentSettings(
                max_num_attempts=2,
                
            ),
        )

    def _get_lambda(
        self,
        config: LambdaConfig,
    ) -> Tuple[lambda_alpha.PythonFunction, Optional[_lambda.FunctionUrl]]:
        python_runtime: _lambda.Runtime = _lambda.Runtime.PYTHON_3_12
        architecture = _lambda.Architecture.X86_64
        bundling_options = lambda_alpha.BundlingOptions(
            asset_excludes=[
                "*.pyc",
                ".*",
                "**/__pycache__",
                "**/*.egg-info/",
                "**/tests",
                "README.md",
                "poetry.toml",
            ],
        )
        index_directory = Path(config.index_directory)
        func = lambda_alpha.PythonFunction(
            self,
            config.construct_id,
            description=config.description,
            entry=index_directory.as_posix(),
            runtime=python_runtime,
            architecture=architecture,
            bundling=bundling_options,
            index=config.index_module_path,
            handler=config.handler,
            timeout=config.timeout,
            memory_size=config.memory_size_mb,
            ephemeral_storage_size=Size.mebibytes(config.ephemeral_storage_size_mb),
            environment=(model_dump_runtime_settings(config.environment) if config.environment else None),
            log_retention=logs.RetentionDays.FIVE_DAYS,
            tracing=config.xray_tracing,
        )
        for secret_name in config.secret_names_to_read or []:
            secret = secretsmanager.Secret.from_secret_name_v2(self, secret_name, secret_name)
            secret.grant_read(func)

        if config.function_url_config:
            if config.function_url_config.invoke_mode == _lambda.InvokeMode.RESPONSE_STREAM:
                func.add_environment("AWS_LWA_INVOKE_MODE", "RESPONSE_STREAM")
            function_url = func.add_function_url(
                cors=_lambda.FunctionUrlCorsOptions(allowed_origins=["*"], allowed_headers=["*"]),
                auth_type=config.function_url_config.auth_type,
                invoke_mode=config.function_url_config.invoke_mode,
            )
            return func, function_url
        return func, None
