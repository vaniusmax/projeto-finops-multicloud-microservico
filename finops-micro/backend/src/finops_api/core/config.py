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
    aws_tenants: str = Field(default="", alias="AWS_TENANTS")
    aws_cli_path: str = Field(default="aws", alias="AWS_CLI_PATH")
    aws_account_names_json: str = Field(
        default=(
            '{"555136764052":"Algar Brain VM","937406753822":"Algar Security",'
            '"595949041525":"Algar Telecom","209663503877":"AlgarAppDEV",'
            '"655629219208":"AlgarAppHOM","669477896728":"AlgarAppPRD",'
            '"518919108570":"AlgarDataLakeDev","149748488652":"Estacao de Experiencias Digitais",'
            '"838968885358":"Gestao de Marketplace DEV","752725527618":"poc-aiops"}'
        ),
        alias="AWS_ACCOUNT_NAMES_JSON",
    )

    azure_management_group_id: str | None = Field(default=None, alias="AZURE_MANAGEMENT_GROUP_ID")
    azure_tenants: str = Field(default="", alias="AZURE_TENANTS")
    azure_api_version: str = Field(default="2023-11-01", alias="AZURE_API_VERSION")
    azure_cli_path: str = Field(default="az", alias="AZURE_CLI_PATH")

    oci_tenant_id: str | None = Field(default=None, alias="OCI_TENANT_ID")
    oci_profile: str = Field(default="DEFAULT", alias="OCI_PROFILE")
    oci_tenants: str = Field(default="", alias="OCI_TENANTS")
    oci_region: str = Field(default="sa-saopaulo-1", alias="OCI_REGION")
    oci_cli_path: str = Field(default="oci", alias="OCI_CLI_PATH")
    tenant_configs_json: str = Field(default="{}", alias="TENANT_CONFIGS_JSON")

    auth_allowed_email_domains: str = Field(
        default="algar.com.br,algartelecom.com.br",
        alias="AUTH_ALLOWED_EMAIL_DOMAINS",
    )
    auth_frontend_base_url: str = Field(default="http://localhost:3000", alias="AUTH_FRONTEND_BASE_URL")
    auth_verify_email_path: str = Field(default="/verify-email", alias="AUTH_VERIFY_EMAIL_PATH")
    auth_session_ttl_hours: int = Field(default=12, alias="AUTH_SESSION_TTL_HOURS")
    auth_verification_ttl_hours: int = Field(default=24, alias="AUTH_VERIFICATION_TTL_HOURS")
    auth_email_from: str = Field(default="finops@algar.com.br", alias="AUTH_EMAIL_FROM")
    smtp_host: str | None = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_username: str | None = Field(default=None, alias="SMTP_USERNAME")
    smtp_password: str | None = Field(default=None, alias="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(default=True, alias="SMTP_USE_TLS")

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
    currency_rate_sync_on_request: bool = Field(default=True, alias="CURRENCY_RATE_SYNC_ON_REQUEST")
    currency_rate_provider_url: str = Field(
        default="https://economia.awesomeapi.com.br/json/daily/USD-BRL/1",
        alias="CURRENCY_RATE_PROVIDER_URL",
    )
    currency_rate_timeout_seconds: float = Field(default=10.0, alias="CURRENCY_RATE_TIMEOUT_SECONDS")
    currency_rate_agno_enabled: bool = Field(default=False, alias="CURRENCY_RATE_AGNO_ENABLED")
    currency_rate_yfinance_enabled: bool = Field(default=True, alias="CURRENCY_RATE_YFINANCE_ENABLED")
    currency_rate_yfinance_symbol: str = Field(default="BRL=X", alias="CURRENCY_RATE_YFINANCE_SYMBOL")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    openai_api_base: str | None = Field(default=None, alias="OPENAI_API_BASE")
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
