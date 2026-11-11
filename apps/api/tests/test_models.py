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
        "trip_participants",
        "expense_shares",
        "trip_invitations",
        "trip_activity",
    }


def test_trip_relationships_are_defined() -> None:
    trip = Base.metadata.tables["trips"]
    assert "user_id" in trip.c
    assert trip.c.user_id.foreign_keys
    assert "trip_id" in Base.metadata.tables["trip_expenses"].c
    assert Base.metadata.tables["trip_expenses"].c.trip_id.foreign_keys
    assert "paid_by_participant_id" in Base.metadata.tables["trip_expenses"].c
    assert Base.metadata.tables["trip_expenses"].c.paid_by_participant_id.foreign_keys
    assert "role" in Base.metadata.tables["trip_participants"].c
    assert "role" in Base.metadata.tables["trip_invitations"].c
    assert "trip_id" in Base.metadata.tables["trip_participants"].c
    assert Base.metadata.tables["trip_participants"].c.trip_id.foreign_keys
    assert Base.metadata.tables["trip_participants"].c.user_id.foreign_keys
    assert "uq_trip_invitations_token_hash" in {
        constraint.name for constraint in Base.metadata.tables["trip_invitations"].constraints
    }
    activity = Base.metadata.tables["trip_activity"]
    assert activity.c.trip_id.foreign_keys
    assert activity.c.actor_user_id.foreign_keys
    assert {"actor_name", "action", "entity_type", "summary", "created_at"} <= set(activity.c.keys())
    shares = Base.metadata.tables["expense_shares"]
    assert shares.c.expense_id.foreign_keys
    assert shares.c.participant_id.foreign_keys
    assert {constraint.name for constraint in shares.constraints} >= {
        "uq_expense_share_participant",
        "ck_expense_share_amount_positive",
    }
