from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from finops_api.core.config import settings
from finops_api.models.dim_tenant import DimTenant


MULTI_TENANT_CLOUDS = {"aws", "azure", "oci"}


@dataclass(frozen=True)
class TenantRuntimeConfig:
    cloud: str
    tenant_key: str
    profile: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class TenantService:
    def __init__(self, db: Session | None = None) -> None:
        self.db = db
        self._configs = self.load_tenants_by_cloud()

    @staticmethod
    def _parse_csv(raw: str) -> list[str]:
        return [item.strip() for item in (raw or "").split(",") if item.strip()]

    @staticmethod
    def _parse_json(raw: str) -> dict[str, Any]:
        if not raw:
            return {}
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        return payload if isinstance(payload, dict) else {}

    @classmethod
    def load_tenants_by_cloud(cls) -> dict[str, list[TenantRuntimeConfig]]:
        config_payload = cls._parse_json(settings.tenant_configs_json)
        clouds: dict[str, list[str]] = {
            "aws": cls._parse_csv(settings.aws_tenants),
            "azure": cls._parse_csv(settings.azure_tenants),
            "oci": cls._parse_csv(settings.oci_tenants),
        }

        resolved: dict[str, list[TenantRuntimeConfig]] = {}
        for cloud, tenant_keys in clouds.items():
            cloud_payload = config_payload.get(cloud) if isinstance(config_payload.get(cloud), dict) else {}
            configs: list[TenantRuntimeConfig] = []
            for tenant_key in tenant_keys:
                metadata = cloud_payload.get(tenant_key) if isinstance(cloud_payload, dict) else {}
                metadata = metadata if isinstance(metadata, dict) else {}
                profile = str(metadata.get("profile") or tenant_key).strip() or tenant_key
                extra_metadata = {key: value for key, value in metadata.items() if key != "profile"}
                configs.append(
                    TenantRuntimeConfig(
                        cloud=cloud,
                        tenant_key=tenant_key,
                        profile=profile,
                        metadata=extra_metadata,
                    )
                )
            resolved[cloud] = configs
        return resolved

    def cloud_has_multi_tenant(self, cloud: str) -> bool:
        cloud_key = (cloud or "").strip().lower()
        return len(self._configs.get(cloud_key, [])) > 1

    def get_runtime_configs(self, cloud: str) -> list[TenantRuntimeConfig]:
        cloud_key = (cloud or "").strip().lower()
        configs = self._configs.get(cloud_key, [])
        if configs:
            return configs

        if cloud_key == "aws" and settings.aws_profile:
            return [TenantRuntimeConfig(cloud="aws", tenant_key=settings.aws_profile, profile=settings.aws_profile)]
        if cloud_key == "azure":
            fallback = settings.azure_management_group_id or "default"
            return [TenantRuntimeConfig(cloud="azure", tenant_key=fallback, profile=fallback)]
        if cloud_key == "oci":
            metadata = {}
            if settings.oci_tenant_id:
                metadata["tenant_id"] = settings.oci_tenant_id
            return [TenantRuntimeConfig(cloud="oci", tenant_key=settings.oci_profile, profile=settings.oci_profile, metadata=metadata)]
        return []

    def require_tenant_key(self, cloud: str, tenant_key: str | None) -> None:
        if cloud == "all":
            return
        if self.cloud_has_multi_tenant(cloud) and not tenant_key:
            raise ValueError(f"tenant_key é obrigatório para {cloud}")

    def sync_configured_tenants(self) -> None:
        if self.db is None:
            return
        for cloud in MULTI_TENANT_CLOUDS:
            for config in self.get_runtime_configs(cloud):
                stmt = insert(DimTenant).values(
                    cloud=cloud,
                    tenant_key=config.tenant_key,
                    tenant_name=config.tenant_key,
                    metadata_json=config.metadata,
                    is_active=True,
                ).on_conflict_do_update(
                    index_elements=[DimTenant.cloud, DimTenant.tenant_key],
                    set_={
                        DimTenant.tenant_name: config.tenant_key,
                        DimTenant.metadata_json: config.metadata,
                        DimTenant.is_active: True,
                    },
                )
                self.db.execute(stmt)
        self.db.commit()

    def list_tenants(self, cloud: str) -> list[DimTenant]:
        if self.db is None:
            raise ValueError("db session é obrigatória para listar tenants")
        self.sync_configured_tenants()
        configured_keys = {config.tenant_key for config in self.get_runtime_configs(cloud)}
        stmt = (
            select(DimTenant)
            .where(DimTenant.cloud == cloud, DimTenant.is_active.is_(True))
            .order_by(DimTenant.tenant_name.asc().nullslast(), DimTenant.tenant_key.asc())
        )
        tenants = list(self.db.execute(stmt).scalars().all())
        if configured_keys:
            tenants = [tenant for tenant in tenants if tenant.tenant_key in configured_keys]
        return tenants

    def resolve_tenant(self, cloud: str, tenant_key: str | None) -> DimTenant | None:
        cloud_key = (cloud or "").strip().lower()
        if cloud_key == "all":
            return None
        if self.db is None:
            raise ValueError("db session é obrigatória para resolver tenant")

        self.sync_configured_tenants()
        self.require_tenant_key(cloud_key, tenant_key)

        if tenant_key:
            stmt = select(DimTenant).where(
                DimTenant.cloud == cloud_key,
                DimTenant.tenant_key == tenant_key,
                DimTenant.is_active.is_(True),
            )
            tenant = self.db.execute(stmt).scalar_one_or_none()
            configured_keys = {config.tenant_key for config in self.get_runtime_configs(cloud_key)}
            if tenant is None or (configured_keys and tenant.tenant_key not in configured_keys):
                raise ValueError(f"tenant_key inválido para {cloud_key}: {tenant_key}")
            return tenant

        tenants = self.list_tenants(cloud_key)
        if len(tenants) == 1:
            return tenants[0]
        return None

    def runtime_config_for(self, cloud: str, tenant_key: str | None) -> TenantRuntimeConfig | None:
        cloud_key = (cloud or "").strip().lower()
        configs = self.get_runtime_configs(cloud_key)
        if tenant_key:
            for config in configs:
                if config.tenant_key == tenant_key:
                    return config
            return None
        if len(configs) == 1:
            return configs[0]
        return None
