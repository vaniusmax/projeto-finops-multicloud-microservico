from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from finops_api.core.config import settings
from finops_api.models.auth_email_verification_token import AuthEmailVerificationToken
from finops_api.models.auth_session import AuthSession
from finops_api.models.auth_user import AuthUser
from finops_api.services.email_service import EmailService


@dataclass(frozen=True)
class AuthSessionPayload:
    access_token: str
    expires_at: datetime
    user: AuthUser


class AuthService:
    def __init__(self, db: Session, email_service: EmailService | None = None) -> None:
        self.db = db
        self.email_service = email_service or EmailService()

    @staticmethod
    def normalize_email(email: str) -> str:
        return email.strip().lower()

    @staticmethod
    def allowed_domains() -> list[str]:
        return [item.strip().lower() for item in settings.auth_allowed_email_domains.split(",") if item.strip()]

    @classmethod
    def ensure_allowed_email_domain(cls, email: str) -> None:
        normalized = cls.normalize_email(email)
        domain = normalized.split("@")[-1]
        if domain not in cls.allowed_domains():
            raise ValueError("Somente e-mails do domínio Algar podem se cadastrar")

    def register_user(self, *, first_name: str, last_name: str, email: str) -> AuthUser:
        normalized_email = self.normalize_email(email)
        self.ensure_allowed_email_domain(normalized_email)

        user = self.db.execute(select(AuthUser).where(AuthUser.email == normalized_email)).scalar_one_or_none()
        if user and user.is_email_verified:
            raise ValueError("Usuário já cadastrado e validado")

        if user is None:
            user = AuthUser(
                first_name=first_name.strip(),
                last_name=last_name.strip(),
                email=normalized_email,
                password_hash=None,
                is_email_verified=False,
                is_active=True,
            )
            self.db.add(user)
            self.db.flush()
        else:
            user.first_name = first_name.strip()
            user.last_name = last_name.strip()

        raw_token = self._issue_verification_token(user)
        verification_url = self.build_verification_url(raw_token)
        self.email_service.send_registration_email(
            recipient=user.email,
            first_name=user.first_name,
            verification_url=verification_url,
        )
        self.db.commit()
        self.db.refresh(user)
        return user

    def verify_email(self, *, token: str, password: str) -> AuthSessionPayload:
        if len(password) < 8:
            raise ValueError("A senha deve ter pelo menos 8 caracteres")

        token_hash = self._hash_token(token)
        record = self.db.execute(
            select(AuthEmailVerificationToken).where(AuthEmailVerificationToken.token_hash == token_hash)
        ).scalar_one_or_none()
        if record is None:
            raise ValueError("Token de verificação inválido")
        if record.consumed_at is not None:
            raise ValueError("Token de verificação já utilizado")
        if record.expires_at <= datetime.now(timezone.utc):
            raise ValueError("Token de verificação expirado")

        user = self.db.get(AuthUser, record.user_id)
        if user is None or not user.is_active:
            raise ValueError("Usuário não encontrado ou inativo")

        user.password_hash = self.hash_password(password)
        user.is_email_verified = True
        record.consumed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(user)
        return self._create_session(user)

    def login(self, *, email: str, password: str) -> AuthSessionPayload:
        normalized_email = self.normalize_email(email)
        user = self.db.execute(select(AuthUser).where(AuthUser.email == normalized_email)).scalar_one_or_none()
        if user is None or not user.is_active:
            raise ValueError("Credenciais inválidas")
        if not user.is_email_verified:
            raise ValueError("Verifique seu e-mail antes de acessar o dashboard")
        if not user.password_hash or not self.verify_password(password, user.password_hash):
            raise ValueError("Credenciais inválidas")
        return self._create_session(user)

    def get_user_by_access_token(self, token: str) -> AuthUser:
        token_hash = self._hash_token(token)
        session = self.db.execute(select(AuthSession).where(AuthSession.token_hash == token_hash)).scalar_one_or_none()
        if session is None:
            raise ValueError("Sessão inválida")
        if session.revoked_at is not None or session.expires_at <= datetime.now(timezone.utc):
            raise ValueError("Sessão expirada")

        session.last_seen_at = datetime.now(timezone.utc)
        self.db.commit()
        user = self.db.get(AuthUser, session.user_id)
        if user is None or not user.is_active:
            raise ValueError("Usuário não encontrado ou inativo")
        return user

    def logout(self, token: str) -> None:
        token_hash = self._hash_token(token)
        session = self.db.execute(select(AuthSession).where(AuthSession.token_hash == token_hash)).scalar_one_or_none()
        if session is None:
            return
        session.revoked_at = datetime.now(timezone.utc)
        self.db.commit()

    def build_verification_url(self, raw_token: str) -> str:
        base = settings.auth_frontend_base_url.rstrip("/")
        path = settings.auth_verify_email_path
        if not path.startswith("/"):
            path = f"/{path}"
        return f"{base}{path}?token={raw_token}"

    def _issue_verification_token(self, user: AuthUser) -> str:
        self.db.execute(
            update(AuthEmailVerificationToken)
            .where(AuthEmailVerificationToken.user_id == user.user_id, AuthEmailVerificationToken.consumed_at.is_(None))
            .values(consumed_at=datetime.now(timezone.utc))
        )
        raw_token = secrets.token_urlsafe(32)
        self.db.add(
            AuthEmailVerificationToken(
                user_id=user.user_id,
                token_hash=self._hash_token(raw_token),
                expires_at=datetime.now(timezone.utc) + timedelta(hours=settings.auth_verification_ttl_hours),
            )
        )
        self.db.flush()
        return raw_token

    def _create_session(self, user: AuthUser) -> AuthSessionPayload:
        raw_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.auth_session_ttl_hours)
        self.db.add(
            AuthSession(
                user_id=user.user_id,
                token_hash=self._hash_token(raw_token),
                expires_at=expires_at,
            )
        )
        self.db.commit()
        self.db.refresh(user)
        return AuthSessionPayload(access_token=raw_token, expires_at=expires_at, user=user)

    @staticmethod
    def hash_password(password: str) -> str:
        salt = os.urandom(16)
        iterations = 390000
        derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return "pbkdf2_sha256${}${}${}".format(
            iterations,
            base64.b64encode(salt).decode("ascii"),
            base64.b64encode(derived).decode("ascii"),
        )

    @staticmethod
    def verify_password(password: str, encoded_hash: str) -> bool:
        try:
            algorithm, iterations_text, salt_text, hash_text = encoded_hash.split("$", 3)
        except ValueError:
            return False
        if algorithm != "pbkdf2_sha256":
            return False
        derived = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            base64.b64decode(salt_text.encode("ascii")),
            int(iterations_text),
        )
        return hmac.compare_digest(base64.b64encode(derived).decode("ascii"), hash_text)

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()
