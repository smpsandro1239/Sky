from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.activity import TripActivity
from app.models.user import User


def record_trip_activity(
    db: Session,
    *,
    trip_id: UUID,
    actor: User,
    action: str,
    entity_type: str,
    entity_id: UUID | str | None,
    summary: str,
) -> None:
    """Regista um evento sem guardar tokens, credenciais ou payloads integrais."""
    actor_name = (actor.display_name or actor.email.split("@", 1)[0]).strip()[:120]
    db.add(
        TripActivity(
            trip_id=trip_id,
            actor_user_id=actor.id,
            actor_name=actor_name or "Utilizador",
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            summary=summary[:240],
            created_at=datetime.now(timezone.utc),
        )
    )
