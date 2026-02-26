from __future__ import annotations

import argparse
from datetime import date

from finops_api.db.session import SessionLocal
from finops_api.services.ingest_service import run_ingest_job


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

    args = parser.parse_args()

    end = date.fromisoformat(args.end) if args.end else date.today()
    start = date.fromisoformat(args.start) if args.start else date(end.year, 1, 1)
    if start > end:
        raise ValueError("start deve ser menor ou igual a end")

    providers = ["aws", "azure", "oci"] if args.provider == "all" else [args.provider]
    with SessionLocal() as session:
        for provider in providers:
            result = run_ingest_job(session, provider=provider, start=start, end=end)
            print(
                f"[{provider}] recebido={result['rows_received']} gravado={result['rows_written']}"
            )


if __name__ == "__main__":
    main()
