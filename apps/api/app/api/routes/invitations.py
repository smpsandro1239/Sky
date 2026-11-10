import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.routes.trips import get_user_trip
from app.models.invitation import TripInvitation
from app.models.participant import TripParticipant
from app.models.user import User
from app.schemas.invitation import (
    InvitationAccept,
    InvitationCreate,
    InvitationCreated,
    InvitationResponse,
)

router = APIRouter(tags=["invitations"])
INVITATION_LIFETIME = timedelta(days=7)


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@router.post(
    "/trips/{trip_id}/invitations",
    response_model=InvitationCreated,
    status_code=status.HTTP_201_CREATED,
)
def create_invitation(
    trip_id: UUID,
    payload: InvitationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> InvitationCreated:
    trip = get_user_trip(db, trip_id, user.id)
    email = str(payload.email).strip().lower()
    if email == user.email.lower():
        raise HTTPException(status_code=409, detail="Não podes convidar a tua própria conta.")
    linked = db.scalar(
        select(TripParticipant.id).where(
            TripParticipant.trip_id == trip.id,
            TripParticipant.user_id == db.scalar(select(User.id).where(User.email == email)),
        )
    ) if db.scalar(select(User.id).where(User.email == email)) is not None else None
    if linked is not None:
        raise HTTPException(status_code=409, detail="Esta pessoa já participa na viagem.")
    pending = db.scalar(
        select(TripInvitation.id).where(
            TripInvitation.trip_id == trip.id,
            TripInvitation.email == email,
            TripInvitation.status == "pending",
            TripInvitation.expires_at > datetime.now(timezone.utc),
        )
    )
    if pending is not None:
        raise HTTPException(status_code=409, detail="Já existe um convite pendente para este email.")

    raw_token = secrets.token_urlsafe(32)
    invitation = TripInvitation(
        trip_id=trip.id,
        invited_by_user_id=user.id,
        email=email,
        token_hash=_token_hash(raw_token),
        status="pending",
        expires_at=datetime.now(timezone.utc) + INVITATION_LIFETIME,
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    data = InvitationResponse.model_validate(invitation).model_dump()
    return InvitationCreated(**data, invitation_token=raw_token)


@router.get(
    "/trips/{trip_id}/invitations",
    response_model=list[InvitationResponse],
)
def list_invitations(
    trip_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[TripInvitation]:
    trip = get_user_trip(db, trip_id, user.id)
    statement = select(TripInvitation).where(
        TripInvitation.trip_id == trip.id
    ).order_by(TripInvitation.created_at.desc())
    return list(db.scalars(statement).all())


@router.delete(
    "/trips/{trip_id}/invitations/{invitation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def revoke_invitation(
    trip_id: UUID,
    invitation_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    trip = get_user_trip(db, trip_id, user.id)
    invitation = db.scalar(
        select(TripInvitation).where(
            TripInvitation.id == invitation_id,
            TripInvitation.trip_id == trip.id,
        )
    )
    if invitation is None:
        raise HTTPException(status_code=404, detail="Convite não encontrado.")
    if invitation.status != "pending":
        raise HTTPException(status_code=409, detail="Só é possível revogar convites pendentes.")
    invitation.status = "revoked"
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/invitations/accept", response_model=InvitationResponse)
def accept_invitation(
    payload: InvitationAccept,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TripInvitation:
    invitation = db.scalar(
        select(TripInvitation).where(TripInvitation.token_hash == _token_hash(payload.token))
    )
    if invitation is None:
        raise HTTPException(status_code=404, detail="Convite inválido ou inexistente.")
    if invitation.status != "pending":
        raise HTTPException(status_code=409, detail="Este convite já não está pendente.")
    now = datetime.now(timezone.utc)
    expires_at = invitation.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= now:
        invitation.status = "expired"
        db.commit()
        raise HTTPException(status_code=410, detail="Este convite expirou.")
    if user.email.strip().lower() != invitation.email:
        raise HTTPException(
            status_code=403,
            detail="Inicia sessão com o endereço de email para o qual o convite foi enviado.",
        )

    existing = db.scalar(
        select(TripParticipant).where(
            TripParticipant.trip_id == invitation.trip_id,
            TripParticipant.email == invitation.email,
        )
    )
    if existing is None:
        participant = TripParticipant(
            trip_id=invitation.trip_id,
            name=user.display_name or user.email.split("@", 1)[0],
            email=user.email,
            user_id=user.id,
        )
        db.add(participant)
    else:
        if existing.user_id not in (None, user.id):
            raise HTTPException(status_code=409, detail="Este participante já está associado a outra conta.")
        existing.user_id = user.id
        existing.email = user.email
        if not existing.name.strip():
            existing.name = user.display_name or user.email.split("@", 1)[0]

    invitation.status = "accepted"
    invitation.accepted_at = now
    db.commit()
    db.refresh(invitation)
    return invitation
