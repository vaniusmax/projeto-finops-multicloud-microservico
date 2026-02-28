from __future__ import annotations

from datetime import date

import httpx

from finops_api.core.config import settings
from finops_api.services.currency_rate_sync_service import CurrencyRateSyncService


class DummyDb:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


class FakeCurrencyRateRepo:
    def __init__(self, exact: float | None = None, historical: float | None = None) -> None:
        self.exact = exact
        self.historical = historical
        self.upserts: list[tuple[date, str, str, float]] = []

    def get_exact_brl_per_usd(self, rate_date: date) -> float | None:
        return self.exact

    def get_brl_per_usd(self, as_of: date) -> float | None:
        return self.historical

    def upsert_rate(self, rate_date: date, from_currency: str, to_currency: str, rate: float) -> None:
        self.upserts.append((rate_date, from_currency, to_currency, rate))


def test_ensure_brl_usd_rate_persists_quote_from_awesomeapi_payload(monkeypatch) -> None:
    monkeypatch.setattr(settings, "currency_rate_sync_on_request", True)
    monkeypatch.setattr(settings, "currency_rate_provider_url", "https://quote.test/usd-brl")

    requested_date = date(2026, 2, 28)
    repo = FakeCurrencyRateRepo()
    db = DummyDb()

    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://quote.test/usd-brl"
        return httpx.Response(
            200,
            json=[{"bid": "5.77", "create_date": "2026-02-28 13:45:00", "code": "USD"}],
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    service = CurrencyRateSyncService(db=db, repo=repo, client=client)

    rate = service.ensure_brl_usd_rate(requested_date)

    assert rate == 5.77
    assert db.commits == 1
    assert repo.upserts == [
        (date(2026, 2, 28), "USD", "BRL", 5.77),
        (date(2026, 2, 28), "BRL", "USD", 1 / 5.77),
    ]


def test_ensure_brl_usd_rate_uses_existing_quote_without_remote_call(monkeypatch) -> None:
    monkeypatch.setattr(settings, "currency_rate_sync_on_request", True)

    repo = FakeCurrencyRateRepo(exact=5.31)
    db = DummyDb()

    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError(f"Unexpected remote call: {request.url}")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    service = CurrencyRateSyncService(db=db, repo=repo, client=client)

    rate = service.ensure_brl_usd_rate(date(2026, 2, 28))

    assert rate == 5.31
    assert db.commits == 0
    assert repo.upserts == []
