from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from finops_api.providers.common import run_cli_with_retry
from finops_api.providers.common.types import CanonicalCostRow


@dataclass(frozen=True)
class OciCliSettings:
    tenant_id: str
    cli_path: str = "oci"
    profile: str = "DEFAULT"
    region: str = "sa-saopaulo-1"
    granularity: str = "DAILY"
    query_type: str = "COST"
    compartment_depth: int = 6
    timeout: int = 300
    retry_attempts: int = 3
    retry_delay: float = 5.0


@dataclass(frozen=True)
class OciTagCostRow:
    """Linha canônica de custo OCI agrupada por tag (namespace+key) e data."""

    usage_date: date
    tag_namespace: str
    tag_key: str
    tag_value: str
    currency_code: str
    amount: Decimal


class OciCliClient:
    def __init__(self, provider_settings: OciCliSettings) -> None:
        if not provider_settings.tenant_id:
            raise ValueError("tenant_id é obrigatório para ingestão OCI")
        self.settings = provider_settings

    def fetch_daily_costs(self, start: date, end: date) -> list[CanonicalCostRow]:
        command = [
            self.settings.cli_path,
            "usage-api",
            "usage-summary",
            "request-summarized-usages",
            "--profile",
            self.settings.profile,
            "--region",
            self.settings.region,
            "--tenant-id",
            self.settings.tenant_id,
            "--time-usage-started",
            self._iso_z(start),
            "--time-usage-ended",
            self._iso_z(end + timedelta(days=1)),
            "--granularity",
            self.settings.granularity,
            "--query-type",
            self.settings.query_type,
            "--group-by",
            json.dumps(["compartmentName", "service", "skuName", "region"]),
            "--compartment-depth",
            str(self.settings.compartment_depth),
            "--output",
            "json",
        ]
        env = os.environ.copy()
        env.setdefault("SUPPRESS_LABEL_WARNING", "True")
        stdout = run_cli_with_retry(
            command,
            timeout=self.settings.timeout,
            max_attempts=self.settings.retry_attempts,
            retry_delay=self.settings.retry_delay,
            env=env,
            label="OCI Usage",
        )
        return self._parse(json.loads(stdout))

    def fetch_daily_tag_costs(
        self,
        start: date,
        end: date,
        tag_namespace: str,
        tag_key: str,
    ) -> list[OciTagCostRow]:
        """Consulta custos OCI agrupados pela tag (namespace+key) por dia.

        Equivalente ao filtro do console OCI Cost Analysis quando se escolhe
        Grouping dimension = Tag, com namespace e key específicos. Faz um único
        chamado ao OCI CLI sem persistência - os dados são consumidos direto
        pelo dashboard.
        """
        ns = (tag_namespace or "").strip()
        key = (tag_key or "").strip()
        if not ns:
            raise ValueError("tag_namespace é obrigatório para tag-cost OCI")
        if not key:
            raise ValueError("tag_key é obrigatório para tag-cost OCI")

        command = [
            self.settings.cli_path,
            "usage-api",
            "usage-summary",
            "request-summarized-usages",
            "--profile",
            self.settings.profile,
            "--region",
            self.settings.region,
            "--tenant-id",
            self.settings.tenant_id,
            "--time-usage-started",
            self._iso_z(start),
            "--time-usage-ended",
            self._iso_z(end + timedelta(days=1)),
            "--granularity",
            self.settings.granularity,
            "--query-type",
            self.settings.query_type,
            "--group-by-tag",
            json.dumps([{"namespace": ns, "key": key}]),
            "--compartment-depth",
            str(self.settings.compartment_depth),
            "--output",
            "json",
        ]
        env = os.environ.copy()
        env.setdefault("SUPPRESS_LABEL_WARNING", "True")
        stdout = run_cli_with_retry(
            command,
            timeout=self.settings.timeout,
            max_attempts=self.settings.retry_attempts,
            retry_delay=self.settings.retry_delay,
            env=env,
            label="OCI Usage tag",
        )
        return self._parse_tag_cost(json.loads(stdout), tag_namespace=ns, tag_key=key)

    def _parse(self, payload: dict[str, Any]) -> list[CanonicalCostRow]:
        rows: list[CanonicalCostRow] = []
        for item in ((payload.get("data") or {}).get("items") or []):
            usage_text = str(item.get("time-usage-started", "")).replace("Z", "+00:00")
            if not usage_text:
                continue
            usage_date = datetime.fromisoformat(usage_text).date()
            service = str(item.get("service") or "Outros")
            compartment = str(item.get("compartment-name") or "Sem compartment")
            sku_name = str(item.get("sku-name") or "Outros")
            item_region = str(item.get("region") or self.settings.region)
            currency = str(
                item.get("currency")
                or item.get("currency-code")
                or item.get("currencyCode")
                or "BRL"
            ).strip().upper() or "BRL"
            amount = Decimal(str(item.get("computed-amount") or "0"))

            rows.append(
                CanonicalCostRow(
                    cloud="oci",
                    usage_date=usage_date,
                    scope_key=compartment,
                    scope_name=compartment,
                    service_key=service,
                    service_name=service,
                    region_key=item_region,
                    region_name=item_region,
                    currency_code=currency,
                    amount=amount,
                    amount_brl=amount if currency.upper() == "BRL" else None,
                    source_ref="oci_usage_cli",
                    metadata_json={"sku_name": sku_name},
                )
            )
        return rows

    def _parse_tag_cost(
        self,
        payload: dict[str, Any],
        *,
        tag_namespace: str,
        tag_key: str,
    ) -> list[OciTagCostRow]:
        rows: list[OciTagCostRow] = []
        for item in ((payload.get("data") or {}).get("items") or []):
            usage_text = str(item.get("time-usage-started", "")).replace("Z", "+00:00")
            if not usage_text:
                continue
            usage_date = datetime.fromisoformat(usage_text).date()

            tag_value = self._extract_tag_value(item, namespace=tag_namespace, key=tag_key)
            currency = str(
                item.get("currency")
                or item.get("currency-code")
                or item.get("currencyCode")
                or "BRL"
            ).strip().upper() or "BRL"
            amount = Decimal(str(item.get("computed-amount") or "0"))

            rows.append(
                OciTagCostRow(
                    usage_date=usage_date,
                    tag_namespace=tag_namespace,
                    tag_key=tag_key,
                    tag_value=tag_value,
                    currency_code=currency,
                    amount=amount,
                )
            )
        return rows

    @staticmethod
    def _extract_tag_value(item: dict[str, Any], *, namespace: str, key: str) -> str:
        """Lê o valor da tag a partir do payload do OCI CLI.

        O CLI da OCI retorna a lista de tags em campos como `tags` (lista de
        objetos com `namespace`, `key`, `value`). Quando o agrupamento usa só
        uma tag, o usual é vir um único item dentro da lista.
        """
        tags = item.get("tags") or []
        if isinstance(tags, list):
            for tag in tags:
                if not isinstance(tag, dict):
                    continue
                tag_ns = str(tag.get("namespace") or "").strip()
                tag_key = str(tag.get("key") or "").strip()
                if tag_ns.lower() == namespace.lower() and tag_key.lower() == key.lower():
                    value = tag.get("value")
                    if value not in (None, ""):
                        return str(value)
        # fallback caso o agrupamento traga colunas planas
        flat_value = item.get(f"{namespace}.{key}") or item.get(key)
        if flat_value not in (None, ""):
            return str(flat_value)
        return "Untagged"

    @staticmethod
    def _iso_z(day: date) -> str:
        dt = datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc)
        return dt.isoformat().replace("+00:00", "Z")
