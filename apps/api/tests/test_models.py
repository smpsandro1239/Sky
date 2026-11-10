from app.database.base import Base
from app import models


def test_initial_models_are_registered() -> None:
    assert set(Base.metadata.tables) == {
        "users",
        "trips",
        "trip_flights",
        "trip_accommodations",
    }


def test_trip_relationships_are_defined() -> None:
    trip = Base.metadata.tables["trips"]
    assert "user_id" in trip.c
    assert trip.c.user_id.foreign_keys
