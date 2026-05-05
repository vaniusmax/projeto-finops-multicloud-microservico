from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from finops_api.core.config import settings
from finops_api.providers.oci.cli_client import (
    OciCliClient,
    OciCliSettings,
    OciTagCostRow,
)
from finops_api.repositories.currency_rate_repo import CurrencyRateRepository
from finops_api.repositories.fact_cost_repo import FactCostRepository
from finops_api.services.tenant_service import TenantService

logger = logging.getLogger(__name__)


OCI_TAG_TENANT_KEY = "OCI-TENANT-ORACLE-SOA"


@dataclass
class OciTagDailyBreakdown:
    """Resultado agregado de custo OCI por tag, dia a dia.

    Pronto para alimentar gráficos do tipo stacked bar (ex.: "Cost by Date" do
    console OCI Cost Analysis com Grouping = Tag).
    """

    items: list[dict]
    tag_values: list[str]
    total_period: float
    currency: str


class OciTagAnalyticsService:
    """Consulta custos OCI agrupados por tag namespace/key direto no OCI CLI.

    Esse serviço é exclusivo da cloud OCI e do tenant ``OCI-TENANT-ORACLE-SOA``
    porque é uma necessidade pontual de FinOps para investigação de custo por
    tag (operation/plataform por padrão). Não há persistência: cada chamada
    aciona o OCI CLI on-demand para refletir os dados mais recentes do
    Cost Analysis.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.tenant_service = TenantService(db)
        self.currency_repo = CurrencyRateRepository(db)
        self.fact_repo = FactCostRepository(db)

    def daily_tag_breakdown(
        self,
        *,
        tenant_key: str,
        start: date,
        end: date,
        currency: str,
        tag_namespace: str,
        tag_key: str,
        top_n: int = 12,
    ) -> OciTagDailyBreakdown:
        if start > end:
            raise ValueError("from deve ser menor ou igual a to")

        normalized_tenant = (tenant_key or "").strip()
        if normalized_tenant.upper() != OCI_TAG_TENANT_KEY:
            raise ValueError(
                "tag-cost OCI está disponível apenas para tenant_key "
                f"{OCI_TAG_TENANT_KEY}"
            )

        runtime_config = self.tenant_service.runtime_config_for("oci", normalized_tenant)
        if runtime_config is None:
            raise ValueError(
                f"tenant OCI {normalized_tenant} não configurado em TENANT_CONFIGS_JSON"
            )
        oci_tenant_id = str(runtime_config.metadata.get("tenant_id") or "")
        if not oci_tenant_id:
            raise ValueError(
                f"tenant_id ausente para o tenant OCI {normalized_tenant}"
            )

        oci_client = OciCliClient(
            OciCliSettings(
                tenant_id=oci_tenant_id,
                cli_path=settings.oci_cli_path,
                profile=runtime_config.profile or settings.oci_profile,
                region=settings.oci_region,
                compartment_depth=settings.oci_compartment_depth,
                timeout=settings.cli_subprocess_timeout,
                retry_attempts=settings.cli_retry_attempts,
                retry_delay=settings.cli_retry_delay,
            )
        )

        rows = oci_client.fetch_daily_tag_costs(
            start=start,
            end=end,
            tag_namespace=tag_namespace,
            tag_key=tag_key,
        )
        return self._aggregate(rows=rows, currency=currency, top_n=top_n, end=end)

    def _aggregate(
        self,
        *,
        rows: list[OciTagCostRow],
        currency: str,
        top_n: int,
        end: date,
    ) -> OciTagDailyBreakdown:
        target_currency = (currency or "BRL").upper()
        brl_per_usd = self._resolve_brl_per_usd(end)

        totals_by_value: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
        per_day: dict[date, dict[str, Decimal]] = defaultdict(lambda: defaultdict(lambda: Decimal("0")))

        for row in rows:
            converted = self._convert_amount(
                amount=row.amount,
                source_currency=row.currency_code,
                target_currency=target_currency,
                brl_per_usd=brl_per_usd,
            )
            tag_value = row.tag_value or "Untagged"
            totals_by_value[tag_value] += converted
            per_day[row.usage_date][tag_value] += converted

        ordered_values = sorted(
            totals_by_value.keys(),
            key=lambda value: float(totals_by_value.get(value, Decimal("0"))),
            reverse=True,
        )
        if len(ordered_values) > top_n:
            top_values = ordered_values[: top_n - 1] if top_n > 1 else ordered_values[:top_n]
            others_values = set(ordered_values) - set(top_values)
        else:
            top_values = ordered_values
            others_values = set()

        items: list[dict] = []
        for usage_date in sorted(per_day.keys()):
            day_bucket = per_day[usage_date]
            by_tag: dict[str, float] = {}
            others_total = Decimal("0")
            day_total = Decimal("0")
            for value, amount in day_bucket.items():
                day_total += amount
                if value in others_values:
                    others_total += amount
                else:
                    by_tag[value] = float(amount)
            if others_values and others_total > 0:
                by_tag["Others"] = float(others_total)
            items.append(
                {
                    "date": usage_date,
                    "total": float(day_total),
                    "byTag": by_tag,
                }
            )

        legend_values = list(top_values)
        if others_values:
            legend_values.append("Others")

        total_period = float(sum(totals_by_value.values()))

        return OciTagDailyBreakdown(
            items=items,
            tag_values=legend_values,
            total_period=total_period,
            currency=target_currency,
        )

    def _resolve_brl_per_usd(self, as_of: date) -> float:
        rate = self.currency_repo.get_brl_per_usd(as_of)
        if rate and rate > 0:
            return float(rate)
        inferred = self.fact_repo.infer_brl_per_usd(
            self._build_inference_filters(as_of)
        )
        if inferred and inferred > 0:
            return float(inferred)
        if settings.usd_rate_fallback and settings.usd_rate_fallback > 0:
            return float(settings.usd_rate_fallback)
        return 1.0

    @staticmethod
    def _build_inference_filters(as_of: date):
        from finops_api.repositories.fact_cost_repo import QueryFilters

        year_start = as_of.replace(month=1, day=1)
        return QueryFilters(cloud="oci", start=year_start, end=as_of, currency="BRL")

    @staticmethod
    def _convert_amount(
        *,
        amount: Decimal,
        source_currency: str,
        target_currency: str,
        brl_per_usd: float,
    ) -> Decimal:
        source = (source_currency or "").upper()
        target = (target_currency or "").upper()
        if source == target:
            return amount
        if source == "USD" and target == "BRL":
            return amount * Decimal(str(brl_per_usd))
        if source == "BRL" and target == "USD":
            if brl_per_usd <= 0:
                return amount
            return amount / Decimal(str(brl_per_usd))
        return amount
