from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app import price_monitor_worker as worker


class FakeRedis:
    def __init__(self, acquire=True):
        self.acquire = acquire
        self.values = {}
        self.expirations = {}

    def set(self, key, value, nx=False, ex=None):
        if nx and key in self.values:
            return False
        if not self.acquire:
            return False
        self.values[key] = value
        self.expirations[key] = ex
        return True

    def expire(self, key, seconds):
        self.expirations[key] = seconds
        return True


class FakeDatabase:
    def __init__(self):
        self.rollbacks = 0

    def rollback(self):
        self.rollbacks += 1


def _search(last_captured_at=None):
    return {
        "user_id": uuid4(),
        "search_type": "flight",
        "search_key": "a" * 64,
        "criteria": {
            "origin": "OPO",
            "destination": "LHR",
            "departure_date": "2099-08-10",
            "adults": 1,
            "currency": "EUR",
            "non_stop": False,
            "max_results": 20,
        },
        "last_captured_at": last_captured_at or datetime.now(timezone.utc) - timedelta(hours=7),
    }


def test_monitor_once_fetches_and_records_when_interval_has_elapsed(monkeypatch):
    search = _search()
    db = FakeDatabase()
    client = FakeRedis()
    recorded = []

    async def fetch(_search):
        return [{"item_key": "flight:stable", "amount": "100.00"}]

    monkeypatch.setattr(worker, "_active_searches", lambda _db: [search])
    monkeypatch.setattr(worker, "_fetch_observations", fetch)
    monkeypatch.setattr(worker, "record_price_observations", lambda *args, **kwargs: recorded.append(kwargs))
    monkeypatch.setattr(worker.settings, "price_monitor_interval_seconds", 21600)

    assert worker.monitor_once(client, db) == 1
    assert len(recorded) == 1
    assert recorded[0]["user_id"] == search["user_id"]
    assert client.expirations[next(iter(client.values))] == 21600
    assert db.rollbacks == 0


def test_monitor_once_skips_a_recent_database_capture(monkeypatch):
    search = _search(datetime.now(timezone.utc) - timedelta(minutes=5))
    db = FakeDatabase()
    client = FakeRedis()
    fetched = []

    async def fetch(_search):
        fetched.append(True)
        return []

    monkeypatch.setattr(worker, "_active_searches", lambda _db: [search])
    monkeypatch.setattr(worker, "_fetch_observations", fetch)
    monkeypatch.setattr(worker.settings, "price_monitor_interval_seconds", 21600)

    assert worker.monitor_once(client, db) == 0
    assert fetched == []
    assert len(client.values) == 1
    assert 1 <= next(iter(client.expirations.values())) <= 21600


def test_monitor_once_respects_existing_redis_lock(monkeypatch):
    search = _search()
    db = FakeDatabase()
    client = FakeRedis(acquire=False)
    fetched = []

    async def fetch(_search):
        fetched.append(True)
        return []

    monkeypatch.setattr(worker, "_active_searches", lambda _db: [search])
    monkeypatch.setattr(worker, "_fetch_observations", fetch)
    monkeypatch.setattr(worker.settings, "price_monitor_interval_seconds", 21600)

    assert worker.monitor_once(client, db) == 0
    assert fetched == []


def test_monitor_once_rolls_back_and_sets_retry_after_provider_error(monkeypatch):
    search = _search()
    db = FakeDatabase()
    client = FakeRedis()

    async def fetch(_search):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(worker, "_active_searches", lambda _db: [search])
    monkeypatch.setattr(worker, "_fetch_observations", fetch)
    monkeypatch.setattr(worker.settings, "price_monitor_interval_seconds", 21600)
    monkeypatch.setattr(worker.settings, "price_monitor_retry_seconds", 600)

    assert worker.monitor_once(client, db) == 0
    assert db.rollbacks == 1
    assert client.expirations[next(iter(client.values))] == 600
