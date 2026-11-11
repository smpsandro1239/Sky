from datetime import datetime, timedelta, timezone
from hashlib import sha256
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import bearer_scheme, get_current_user, get_db
from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password, decode_access_token
from app.models.auth_session import AuthSession
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> User:
    email = str(payload.email).strip().lower()
    user = User(
        email=email,
        display_name=payload.display_name.strip(),
        password_hash=hash_password(payload.password),
        role="traveler",
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Não foi possível criar a conta com estes dados.")
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == str(payload.email).strip().lower()))
    if (
        user is None
        or not user.is_active
        or user.password_hash is None
        or not verify_password(payload.password, user.password_hash)
    ):
        raise HTTPException(status_code=401, detail="Email ou palavra-passe inválidos.")

    now = datetime.now(timezone.utc)
    session_id = uuid4()
    expires_at = now + timedelta(minutes=settings.access_token_minutes)
    token = create_access_token(str(user.id), str(session_id))
    db.add(
        AuthSession(
            id=session_id,
            user_id=user.id,
            token_hash=sha256(token.encode("utf-8")).hexdigest(),
            expires_at=expires_at,
        )
    )
    db.commit()
    return TokenResponse(access_token=token, expires_in=settings.access_token_minutes * 60)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    payload = decode_access_token(credentials.credentials) if credentials else None
    if payload is None:
        raise HTTPException(status_code=401, detail="Autenticação inválida ou expirada.")
    try:
        session_id = UUID(payload["sid"])
    except (KeyError, ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Autenticação inválida ou expirada.")
    auth_session = db.scalar(
        select(AuthSession).where(AuthSession.id == session_id, AuthSession.user_id == user.id)
    )
    if auth_session is not None and auth_session.revoked_at is None:
        auth_session.revoked_at = datetime.now(timezone.utc)
        db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)) -> User:
    return user
