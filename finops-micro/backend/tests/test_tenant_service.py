from __future__ import annotations

from uuid import uuid4

from finops_api.models.dim_tenant import DimTenant
from finops_api.services.tenant_service import TenantService


class FakeScalarResult:
    def __init__(self, value) -> None:
        self.value = value

    def scalar_one_or_none(self):
        return self.value

    def scalars(self):
        return self

    def all(self):
        return [self.value] if self.value is not None else []


class FakeSession:
    def __init__(self, value) -> None:
        self.value = value

    def execute(self, stmt):
        self.last_stmt = str(stmt)
        return FakeScalarResult(self.value)

    def commit(self):
        return None

    def add(self, _value):
        return None


def test_load_tenants_by_cloud_parses_csv_and_json(monkeypatch) -> None:
    monkeypatch.setattr("finops_api.services.tenant_service.settings.aws_tenants", "payer-a,payer-b")
    monkeypatch.setattr("finops_api.services.tenant_service.settings.azure_tenants", "")
    monkeypatch.setattr("finops_api.services.tenant_service.settings.oci_tenants", "OCI-TENANT-OCVS")
    monkeypatch.setattr(
        "finops_api.services.tenant_service.settings.tenant_configs_json",
        '{"oci":{"OCI-TENANT-OCVS":{"profile":"OCI-TENANT-OCVS","tenant_id":"ocid1.tenancy.oc1..example"}}}',
    )

    configs = TenantService.load_tenants_by_cloud()

    assert [item.tenant_key for item in configs["aws"]] == ["payer-a", "payer-b"]
    assert configs["oci"][0].profile == "OCI-TENANT-OCVS"
    assert configs["oci"][0].metadata["tenant_id"] == "ocid1.tenancy.oc1..example"


def test_resolve_tenant_returns_tenant_id_for_explicit_key(monkeypatch) -> None:
    tenant = DimTenant(
        tenant_id=uuid4(),
        cloud="oci",
        tenant_key="OCI-TENANT-OCVS",
        tenant_name="OCI-TENANT-OCVS",
        metadata_json={},
        is_active=True,
    )
    service = TenantService(FakeSession(tenant))
    monkeypatch.setattr(service, "sync_configured_tenants", lambda: None)

    resolved = service.resolve_tenant("oci", "OCI-TENANT-OCVS")

    assert resolved is not None
    assert resolved.tenant_id == tenant.tenant_id
