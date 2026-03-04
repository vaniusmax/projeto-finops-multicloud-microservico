from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from finops_api.db.session import get_db
from finops_api.models.auth_user import AuthUser
from finops_api.schemas.auth import (
    AuthSessionResponse,
    AuthUserResponse,
    LoginRequest,
    RegisterUserRequest,
    RegisterUserResponse,
    VerifyEmailRequest,
)
from finops_api.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _extract_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Cabeçalho Authorization é obrigatório")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization deve usar Bearer token")
    return token.strip()


def _serialize_user(user: AuthUser) -> AuthUserResponse:
    return AuthUserResponse(
        userId=str(user.user_id),
        firstName=user.first_name,
        lastName=user.last_name,
        email=user.email,
        isEmailVerified=user.is_email_verified,
    )


def _serialize_session(result) -> AuthSessionResponse:
    return AuthSessionResponse(
        accessToken=result.access_token,
        expiresAt=result.expires_at,
        user=_serialize_user(result.user),
    )


@router.post("/register", response_model=RegisterUserResponse)
def register_user(payload: RegisterUserRequest, db: Session = Depends(get_db)) -> RegisterUserResponse:
    user = AuthService(db).register_user(
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
    )
    return RegisterUserResponse(
        status="pending_verification",
        email=user.email,
        message="Enviamos um e-mail para concluir seu cadastro no dashboard.",
    )


@router.post("/verify-email", response_model=AuthSessionResponse)
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)) -> AuthSessionResponse:
    session = AuthService(db).verify_email(token=payload.token, password=payload.password)
    return _serialize_session(session)


@router.post("/login", response_model=AuthSessionResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthSessionResponse:
    session = AuthService(db).login(email=payload.email, password=payload.password)
    return _serialize_session(session)


@router.get("/me", response_model=AuthUserResponse)
def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> AuthUserResponse:
    token = _extract_bearer_token(authorization)
    try:
        user = AuthService(db).get_user_by_access_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return _serialize_user(user)


@router.post("/logout")
def logout(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    token = _extract_bearer_token(authorization)
    try:
        AuthService(db).logout(token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return {"status": "ok"}
