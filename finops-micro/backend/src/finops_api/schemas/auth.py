from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AuthUserResponse(BaseModel):
    userId: str
    firstName: str
    lastName: str
    email: str
    isEmailVerified: bool


class RegisterUserRequest(BaseModel):
    first_name: str = Field(min_length=2, max_length=128)
    last_name: str = Field(min_length=2, max_length=128)
    email: str = Field(min_length=6, max_length=320)


class RegisterUserResponse(BaseModel):
    status: str
    email: str
    message: str


class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=16)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(min_length=6, max_length=320)
    password: str = Field(min_length=8, max_length=128)


class AuthSessionResponse(BaseModel):
    accessToken: str
    expiresAt: datetime
    user: AuthUserResponse
