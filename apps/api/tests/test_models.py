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
        "trip_settlements",
        "hotel_favorites",
        "participant_budgets",
        "trip_budget_plans",
        "price_observations",
        "price_alerts",
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
    favorites = Base.metadata.tables["hotel_favorites"]
    assert favorites.c.user_id.foreign_keys
    assert {"hotel_id", "hotel_name", "location", "provider"} <= set(favorites.c.keys())
    assert "uq_hotel_favorites_user_hotel" in {constraint.name for constraint in favorites.constraints}
    plans = Base.metadata.tables["trip_budget_plans"]
    assert plans.c.trip_id.foreign_keys
    assert {"month", "category", "amount", "currency", "created_at", "updated_at"} <= set(plans.c.keys())
    assert "uq_trip_budget_plans_trip_month_category_currency" in {constraint.name for constraint in plans.constraints}
    budgets = Base.metadata.tables["participant_budgets"]
    assert budgets.c.trip_id.foreign_keys
    assert budgets.c.participant_id.foreign_keys
    assert {"amount", "currency", "created_at", "updated_at"} <= set(budgets.c.keys())
    assert "uq_participant_budgets_participant_currency" in {constraint.name for constraint in budgets.constraints}
    price_observations = Base.metadata.tables["price_observations"]
    assert price_observations.c.user_id.foreign_keys
    assert {"capture_id", "search_type", "search_key", "item_key", "amount", "currency", "captured_at"} <= set(price_observations.c.keys())
    price_alerts = Base.metadata.tables["price_alerts"]
    assert price_alerts.c.user_id.foreign_keys
    assert {"search_type", "search_key", "item_key", "currency", "target_price", "is_active", "triggered_price", "triggered_at"} <= set(price_alerts.c.keys())

    shares = Base.metadata.tables["expense_shares"]
    assert shares.c.expense_id.foreign_keys
    assert shares.c.participant_id.foreign_keys
    assert {constraint.name for constraint in shares.constraints} >= {
        "uq_expense_share_participant",
        "ck_expense_share_amount_positive",
    }
