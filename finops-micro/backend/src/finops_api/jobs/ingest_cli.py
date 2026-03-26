from __future__ import annotations

import argparse
from datetime import date

from finops_api.db.session import SessionLocal
from finops_api.services.currency_rate_sync_service import CurrencyRateSyncService
from finops_api.services.ingest_service import run_ingest_job
from finops_api.services.tenant_service import TenantService


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingestao de custos no schema canonico via CLIs dos cloud providers"
    )
    subparsers = parser.add_subparsers(dest="mode", required=True)

    parser_providers = subparsers.add_parser("providers", help="Ingestao via CLIs dos cloud providers")
    parser_providers.add_argument(
        "--provider",
        required=True,
        choices=["aws", "azure", "oci", "all"],
        help="Provider alvo ou all",
    )
    parser_providers.add_argument("--start", required=False, help="Data inicial YYYY-MM-DD")
    parser_providers.add_argument("--end", required=False, help="Data final YYYY-MM-DD")
    parser_providers.add_argument("--tenant-key", required=False, default=None, help="Tenant key (obrigatorio em multi-tenant)")

    args = parser.parse_args()

    end = date.fromisoformat(args.end) if args.end else date.today()
    start = date.fromisoformat(args.start) if args.start else date(end.year, 1, 1)
    if start > end:
        raise ValueError("start deve ser menor ou igual a end")

    providers = ["aws", "azure", "oci"] if args.provider == "all" else [args.provider]
    with SessionLocal() as session:
        tenant_service = TenantService(session)
        for provider in providers:
            tenant_keys = _resolve_tenant_keys(tenant_service, provider, args.tenant_key)
            for tenant_key in tenant_keys:
                result = run_ingest_job(session, provider=provider, start=start, end=end, tenant_key=tenant_key)
                print(
                    f"[{provider}/{result.get('tenant_key', tenant_key)}] "
                    f"recebido={result['rows_received']} gravado={result['rows_written']} "
                    f"inserido={result.get('rows_inserted', 0)} deletado={result.get('rows_deleted', 0)}"
                )
        rate = CurrencyRateSyncService(session).ensure_brl_usd_rate(end)
        if rate is not None:
            print(f"[currency] USD/BRL em {end.isoformat()} = {rate:.6f}")


def _resolve_tenant_keys(tenant_service: TenantService, provider: str, requested_key: str | None) -> list[str | None]:
    if requested_key:
        return [requested_key]
    configs = tenant_service.get_runtime_configs(provider)
    if configs:
        return [c.tenant_key for c in configs]
    return [None]


if __name__ == "__main__":
    main()
