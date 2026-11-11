from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.user import User
from app.schemas.admin import AdminUserResponse, PlatformRoleUpdate

router = APIRouter(prefix="/admin", tags=["platform administration"])


@router.get("/users", response_model=list[AdminUserResponse])
def list_platform_users(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(require_roles("support", "admin")),
    db: Session = Depends(get_db),
) -> list[User]:
    statement = select(User).order_by(User.created_at.desc(), User.id.desc()).offset(offset).limit(limit)
    return list(db.scalars(statement).all())


@router.patch("/users/{user_id}/role", response_model=AdminUserResponse)
def change_platform_role(
    user_id: UUID,
    payload: PlatformRoleUpdate,
    actor: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
) -> User:
    # Serialize role demotions against the complete active-admin set. Locking
    # only the target row would allow two administrators to demote each other
    # concurrently, with both transactions observing the same admin count.
    if payload.role != "admin":
        db.scalars(
            select(User)
            .where(User.role == "admin", User.is_active.is_(True))
            .order_by(User.id)
            .with_for_update()
        ).all()

    target = db.scalar(
        select(User).where(User.id == user_id).with_for_update().execution_options(populate_existing=True)
    )
    if target is None:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado.")

    if target.id == actor.id and payload.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não podes remover o teu próprio papel de administrador.",
        )

    if target.role == "admin" and payload.role != "admin":
        admin_count = db.scalar(
            select(func.count(User.id)).where(User.role == "admin", User.is_active.is_(True))
        ) or 0
        if target.is_active and admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Não é possível remover o último administrador ativo.",
            )

    target.role = payload.role
    db.commit()
    db.refresh(target)
    return target
