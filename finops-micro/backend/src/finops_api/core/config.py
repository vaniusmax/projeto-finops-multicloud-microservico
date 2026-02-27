from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FinOps Micro API"
    app_env: str = "dev"
    debug: bool = False

    api_prefix: str = "/api/v1"
    cors_origins: str = Field(default="http://localhost:3000")
    cors_origin_regex: str | None = Field(
        default=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
        alias="CORS_ORIGIN_REGEX",
    )
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

    target_monthly_brl: float = Field(default=331894.50, alias="TARGET_MONTHLY_BRL")
    target_weekly_brl: float = Field(default=82973.625, alias="TARGET_WEEKLY_BRL")
    target_monthly_usd: float = Field(default=57000.0, alias="TARGET_MONTHLY_USD")
    target_weekly_usd: float = Field(default=5500.0, alias="TARGET_WEEKLY_USD")
    monthly_targets_json: str = Field(
        default=(
            '{"aws":{"2026-01":138531.58,"2026-02":138531.58,"2026-03":138531.58,"2026-04":138531.58,'
            '"2026-05":138531.58,"2026-06":138531.58,"2026-07":138531.58,"2026-08":138531.58,'
            '"2026-09":138531.58,"2026-10":138531.58,"2026-11":138531.58,"2026-12":138531.58},'
            '"azure":{"2026-01":167000.0,"2026-02":167000.0,"2026-03":175519.39,"2026-04":175519.39,'
            '"2026-05":175519.39,"2026-06":175519.39,"2026-07":175519.39,"2026-08":175519.39,'
            '"2026-09":175519.39,"2026-10":175519.39,"2026-11":175519.39,"2026-12":175519.39}}'
        ),
        alias="MONTHLY_TARGETS_JSON",
    )
    usd_rate_fallback: float | None = Field(default=5.1394, alias="USD_RATE_FALLBACK")

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
