from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FinOps Micro API"
    app_env: str = "dev"
    debug: bool = False

    api_prefix: str = "/api/v1"
    cors_origins: str = Field(default="http://localhost:3000")
    auto_ingest_on_request: bool = Field(default=True, alias="AUTO_INGEST_ON_REQUEST")

    database_url: str = Field(
        default="postgresql+psycopg2://finops:finops@localhost:5432/finops",
        alias="DATABASE_URL",
    )

    aws_profile: str | None = Field(default=None, alias="AWS_PROFILE")
    aws_cli_path: str = Field(default="aws", alias="AWS_CLI_PATH")

    azure_management_group_id: str | None = Field(default=None, alias="AZURE_MANAGEMENT_GROUP_ID")
    azure_api_version: str = Field(default="2023-11-01", alias="AZURE_API_VERSION")
    azure_cli_path: str = Field(default="az", alias="AZURE_CLI_PATH")

    oci_tenant_id: str | None = Field(default=None, alias="OCI_TENANT_ID")
    oci_profile: str = Field(default="DEFAULT", alias="OCI_PROFILE")
    oci_region: str = Field(default="sa-saopaulo-1", alias="OCI_REGION")
    oci_cli_path: str = Field(default="oci", alias="OCI_CLI_PATH")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


settings = Settings()
