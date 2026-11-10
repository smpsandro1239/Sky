from app.database.base import Base
from app import models


def test_initial_models_are_registered() -> None:
    assert set(Base.metadata.tables) == {
        "users",
        "auth_identities",
        "trips",
        "trip_flights",
        "trip_accommodations",
        "trip_expenses",
    }


def test_trip_relationships_are_defined() -> None:
    trip = Base.metadata.tables["trips"]
    assert "user_id" in trip.c
    assert trip.c.user_id.foreign_keys
    assert "trip_id" in Base.metadata.tables["trip_expenses"].c
    assert Base.metadata.tables["trip_expenses"].c.trip_id.foreign_keys
