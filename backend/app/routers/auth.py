from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from backend.app.config import JWT_SECRET
from backend.app.database import SessionLocal
from backend.app.models import EmailVerificationToken, RefreshToken, User
from backend.app.schemas import UserCreate, UserResponse, RefreshTokenRequest
from backend.app.security import (
    create_access_token,
    create_refresh_token,
    generate_verification_token,
    hash_password,
    hash_verification_token,
    verify_password,
)
from backend.services.send_email import send_verification_email


router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = HTTPBearer()
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme)
) -> User:
    access_token = credentials.credentials
    try:
        payload = jwt.decode(
            access_token,
            JWT_SECRET,  # type: ignore
            algorithms=["HS256"],
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        )

    user_id = int(payload["sub"])
    with SessionLocal() as db:
        user = db.get(User, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token",
            )
    return user

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate):
    with SessionLocal() as db:
        stmt = select(User).where(User.email == user_data.email)
        exists = db.execute(stmt).scalar_one_or_none()
        if exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="email already registered",
            )

        user = User(
            email=user_data.email,
            password_hash=hash_password(user_data.password),
            email_verified=False,
        )
        db.add(user)
        db.commit()
    return user


@router.post("/send_email")
def send_email(user_data: UserCreate):
    with SessionLocal() as db:
        stmt = select(User).where(User.email == user_data.email)
        user = db.execute(stmt).scalar_one_or_none()
        if not user:
            return {"message": "Verification email sent!"}

        if user.email_verified:
            return {"message": "Already verified!"}

        stmt = select(EmailVerificationToken).where(
            EmailVerificationToken.user_id == user.id,
            EmailVerificationToken.used_at.is_(None),
        )
        existing_tokens = db.execute(stmt).scalars().all()
        now = datetime.now(timezone.utc)

        for existing_token in existing_tokens:
            existing_token.used_at = now

        token = generate_verification_token()
        verification_token = EmailVerificationToken(
            user_id=user.id,
            token_hash=hash_verification_token(token),
            expires_at=now + timedelta(hours=24),
        )
        db.add(verification_token)
        db.commit()

    send_verification_email(user_data.email, token)
    return {"message": "Verification email sent!"}


@router.get("/verify-email")
def verify_email(token: str):
    with SessionLocal() as db:
        token_hash = hash_verification_token(token)
        stmt = select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == token_hash
        )
        verification_token = db.execute(stmt).scalar_one_or_none()

        if verification_token is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token",
            )

        if verification_token.used_at is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification token has already been used",
            )

        now = datetime.now(timezone.utc)
        if verification_token.expires_at < now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification token has expired",
            )

        user = db.get(User, verification_token.user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User associated with token does not exist",
            )

        user.email_verified = True
        verification_token.used_at = now
        db.commit()

    return {"message": "Email verified successfully"}


@router.post("/login")
def login(user_data: UserCreate) -> dict:
    with SessionLocal() as db:
        user = db.execute(
            select(User).where(User.email == user_data.email)
        ).scalar_one_or_none()

        if user is None or not verify_password(user_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid credentials",
            )

        if not user.email_verified:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not verified",
            )

        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token()
        now = datetime.now(timezone.utc)
        refresh_token_record = RefreshToken(
            user_id=user.id,
            token_hash=hash_verification_token(refresh_token),
            expires_at=now + timedelta(days=30),
            created_at=now,
        )
        db.add(refresh_token_record)
        db.commit()
        db.refresh(refresh_token_record)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }


@router.post("/refresh")
def refresh_token(request: RefreshTokenRequest) -> dict:
    with SessionLocal() as db:
        token = db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash
                == hash_verification_token(request.refresh_token)
            )
        ).scalar_one_or_none()

        if token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        if token.revoked_at is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked",
            )

        now = datetime.now(timezone.utc)
        if token.expires_at < now:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired",
            )

        user = db.get(User, token.user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        return {
            "access_token": create_access_token(user.id),
            "token_type": "bearer",
        }


@router.post("/logout")
def logout(request: RefreshTokenRequest) -> dict:
    with SessionLocal() as db:
        token = db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash
                == hash_verification_token(request.refresh_token)
            )
        ).scalar_one_or_none()

        if token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        if token.revoked_at is not None:
            return {"message": "Already logged out"}

        token.revoked_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(token)
        return {"message": "Logout successful"}


