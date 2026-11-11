from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.participant import TripParticipant
from app.models.trip import Trip


def add_notification(
    db: Session,
    *,
    user_id: UUID,
    notification_type: str,
    title: str,
    message: str,
    metadata: dict,
    link: str = "/dashboard",
) -> None:
    """Adiciona uma notificação privada à transação actual."""
    db.add(
        Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            link=link,
            metadata_json=metadata,
        )
    )


def notify_trip_members(
    db: Session,
    *,
    trip: Trip,
    actor_user_id: UUID,
    notification_type: str,
    title: str,
    message: str,
    metadata: dict,
) -> None:
    """Notifica os membros com conta associada, excluindo quem executou a acção."""
    recipients = set(
        db.scalars(
            select(TripParticipant.user_id).where(
                TripParticipant.trip_id == trip.id,
                TripParticipant.user_id.is_not(None),
                TripParticipant.user_id != actor_user_id,
            )
        ).all()
    )
    if trip.user_id != actor_user_id:
        recipients.add(trip.user_id)

    for recipient_id in recipients:
        add_notification(
            db,
            user_id=recipient_id,
            notification_type=notification_type,
            title=title,
            message=message,
            metadata={**metadata, "trip_id": str(trip.id)},
            link=f"/dashboard/{trip.id}",
        )
