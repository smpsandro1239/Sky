from uuid import uuid4

from app.services.price_intelligence import build_search_fingerprint, record_price_observations


class FakeSession:
    def __init__(self):
        self.rows = []
        self.committed = False

    def add_all(self, rows):
        self.rows.extend(rows)

    def commit(self):
        self.committed = True


def test_search_fingerprint_is_stable_and_ignores_dictionary_order():
    first = {"origin": "OPO", "departure_date": "2027-08-10", "adults": 2}
    second = {"adults": 2, "departure_date": "2027-08-10", "origin": "OPO"}

    assert build_search_fingerprint("flight", first) == build_search_fingerprint("flight", second)
    assert build_search_fingerprint("flight", first) != build_search_fingerprint(
        "hotel", first
    )


def test_record_price_observations_stores_only_valid_provider_prices():
    db = FakeSession()
    user_id = uuid4()
    criteria = {"origin": "OPO", "destination": "LHR"}
    observations = [
        {
            "item_key": "offer-1",
            "item_name": "OPO → LHR",
            "provider": "amadeus",
            "amount": "123.45",
            "currency": "EUR",
            "is_available": True,
        },
        {
            "item_key": "invalid",
            "item_name": "Invalid offer",
            "provider": "amadeus",
            "amount": "-1",
            "currency": "EUR",
        },
    ]

    search_key = record_price_observations(
        db,
        user_id=user_id,
        search_type="flight",
        criteria=criteria,
        observations=observations,
    )

    assert len(search_key) == 64
    assert len(db.rows) == 1
    assert db.rows[0].user_id == user_id
    assert db.rows[0].amount == 123.45
    assert db.rows[0].search_key == search_key
    assert db.rows[0].search_criteria == criteria
    assert db.committed is True


def test_empty_capture_returns_fingerprint_without_database_write():
    db = FakeSession()

    search_key = record_price_observations(
        db,
        user_id=uuid4(),
        search_type="hotel",
        criteria={"city_code": "DXB"},
        observations=[],
    )

    assert len(search_key) == 64
    assert db.rows == []
    assert db.committed is False
