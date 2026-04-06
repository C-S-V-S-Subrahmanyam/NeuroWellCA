"""
Authentication routes for FastAPI
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import uuid4
import random
import logging

from src.models.database import get_db
from src.models.models import User, Role, PendingSignupOTP
from src.utils.config import settings
from src.services.permission_service import PermissionService
from src.services.email_service import send_email_with_template

logger = logging.getLogger(__name__)

router = APIRouter()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# Pydantic models
class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    age: Optional[int] = None
    guardian_contact: Optional[str] = None
    guardian_email: Optional[EmailStr] = None


class UserLogin(BaseModel):
    username: str
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    requires_assessment: bool = False
    requires_email_verification: bool = False


class OTPStartResponse(BaseModel):
    message: str
    email: EmailStr
    otp_expires_minutes: int


class SignupOTPVerifyRequest(BaseModel):
    email: EmailStr
    otp: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    age: Optional[int]
    guardian_contact: Optional[str]
    guardian_email: Optional[EmailStr]
    has_completed_initial_assessment: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Helper functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    # Ensure sub is string
    if "sub" in to_encode and not isinstance(to_encode["sub"], str):
        to_encode["sub"] = str(to_encode["sub"])
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    
    # Ensure sub is string
    if "sub" in to_encode and not isinstance(to_encode["sub"], str):
        to_encode["sub"] = str(to_encode["sub"])
    
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        
        # Convert string user_id to int
        user_id = int(user_id_str)
    except (JWTError, ValueError, TypeError) as e:
        logger.error(f"❌ Token validation failed: {e}")
        raise credentials_exception
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception

    token_version = payload.get("token_version")
    user_token_version = user.token_version or 1
    if token_version is not None and user_token_version != token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is no longer valid. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


# Routes
@router.post("/register", response_model=OTPStartResponse, status_code=status.HTTP_200_OK)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    """Start signup by sending OTP to email."""
    try:
        # Check if username/email already belongs to a real user.
        result = await db.execute(select(User).where(User.username == user_data.username))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )

        result = await db.execute(select(User).where(User.email == user_data.email))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )

        # Prevent username collisions across pending requests.
        pending_username_result = await db.execute(
            select(PendingSignupOTP).where(PendingSignupOTP.username == user_data.username)
        )
        pending_username = pending_username_result.scalar_one_or_none()
        if pending_username and pending_username.email != user_data.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username is reserved by another pending signup"
            )

        otp_code = f"{random.randint(0, 999999):06d}"
        otp_expires_at = datetime.utcnow() + timedelta(minutes=10)

        pending_email_result = await db.execute(
            select(PendingSignupOTP).where(PendingSignupOTP.email == user_data.email)
        )
        pending = pending_email_result.scalar_one_or_none()

        if pending:
            pending.username = user_data.username
            pending.password_hash = get_password_hash(user_data.password)
            pending.full_name = user_data.full_name
            pending.age = user_data.age
            pending.guardian_contact = user_data.guardian_contact
            pending.guardian_email = user_data.guardian_email
            pending.otp_code = otp_code
            pending.otp_expires_at = otp_expires_at
            pending.otp_attempts = 0
        else:
            pending = PendingSignupOTP(
                username=user_data.username,
                email=user_data.email,
                password_hash=get_password_hash(user_data.password),
                full_name=user_data.full_name,
                age=user_data.age,
                guardian_contact=user_data.guardian_contact,
                guardian_email=user_data.guardian_email,
                otp_code=otp_code,
                otp_expires_at=otp_expires_at,
                otp_attempts=0,
            )
            db.add(pending)

        content_html = (
            "<p style='margin:0 0 14px;'>Use the one-time code below to verify your NeuroWell account:</p>"
            f"<div style='margin:6px 0 18px;display:inline-block;padding:10px 16px;"
            "font-size:28px;font-weight:700;letter-spacing:4px;background:#dbeafe;color:#1e3a8a;border-radius:12px;'>"
            f"{otp_code}</div>"
            "<p style='margin:0 0 8px;'>This code expires in <strong>10 minutes</strong>.</p>"
            "<p style='margin:0;color:#475569;'>If you did not request this, please ignore this email.</p>"
        )
        plain_text = (
            f"Your NeuroWell OTP is: {otp_code}\n"
            "This code expires in 10 minutes.\n"
            "If you did not request this, you can ignore this email."
        )

        sent, reason = send_email_with_template(
            to_email=user_data.email,
            subject="NeuroWell Signup Verification OTP",
            title="Verify Your NeuroWell Account",
            subtitle="Secure signup confirmation",
            content_html=content_html,
            plain_text=plain_text,
        )

        if not sent:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Unable to send OTP email ({reason})"
            )

        await db.commit()
        logger.info("✅ Signup OTP sent to %s", user_data.email)

        return OTPStartResponse(
            message="OTP sent to email. Verify to complete signup.",
            email=user_data.email,
            otp_expires_minutes=10,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Signup OTP initiation failed"
        )


@router.post("/verify-signup-otp", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def verify_signup_otp(payload: SignupOTPVerifyRequest, db: AsyncSession = Depends(get_db)):
    """Verify OTP and create user account."""
    try:
        result = await db.execute(select(PendingSignupOTP).where(PendingSignupOTP.email == payload.email))
        pending = result.scalar_one_or_none()
        if not pending:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No pending signup found for this email"
            )

        if pending.otp_expires_at < datetime.utcnow():
            await db.delete(pending)
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP expired. Please register again to receive a new code"
            )

        if pending.otp_code != payload.otp.strip():
            pending.otp_attempts = (pending.otp_attempts or 0) + 1
            if pending.otp_attempts >= 5:
                await db.delete(pending)
                await db.commit()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Too many invalid OTP attempts. Please register again"
                )
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OTP"
            )

        # Final uniqueness checks to avoid race conditions.
        username_exists = await db.execute(select(User).where(User.username == pending.username))
        if username_exists.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Username already exists")

        email_exists = await db.execute(select(User).where(User.email == pending.email))
        if email_exists.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already exists")

        new_user = User(
            username=pending.username,
            email=pending.email,
            password_hash=pending.password_hash,
            full_name=pending.full_name,
            age=pending.age,
            guardian_contact=pending.guardian_contact,
            guardian_email=pending.guardian_email,
            has_completed_initial_assessment=False,
            email_verified=True,
        )
        db.add(new_user)
        await db.flush()

        try:
            role_result = await db.execute(select(Role).where(Role.code == "patient"))
            patient_role = role_result.scalar_one_or_none()
            if patient_role:
                await PermissionService.assign_role_to_user(
                    db=db,
                    user_id=new_user.id,
                    role_id=patient_role.id,
                )
            else:
                logger.warning("⚠️ 'patient' role not found in database")
        except Exception as perm_error:
            logger.error("❌ Failed to assign default role: %s", perm_error)

        await db.delete(pending)
        await db.commit()
        await db.refresh(new_user)

        logger.info("✅ New user created after OTP verification: %s", new_user.username)
        return new_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ OTP verification failed: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OTP verification failed"
        )


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """User login"""
    try:
        # Find user
        result = await db.execute(select(User).where(User.username == user_data.username))
        user = result.scalar_one_or_none()
        
        if not user or not verify_password(user_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Update last login
        if user.token_version is None:
            user.token_version = 1
        user.last_login = datetime.utcnow()
        await db.commit()

        email_verified = getattr(user, 'email_verified', True)
        if not email_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email not verified. Complete OTP verification first.",
            )
        
        # Create tokens
        access_token = create_access_token(data={
            "sub": str(user.id),
            "token_version": user.token_version or 1,
            "jti": str(uuid4()),
        })
        refresh_token = create_refresh_token(data={
            "sub": str(user.id),
            "token_version": user.token_version or 1,
            "jti": str(uuid4()),
        })
        
        logger.info(f"✅ User logged in: {user.username}")
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            requires_assessment=not user.has_completed_initial_assessment,
            requires_email_verification=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    age: Optional[int] = None
    guardian_contact: Optional[str] = None
    guardian_email: Optional[EmailStr] = None


@router.put("/profile")
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user profile"""
    try:
        # Update fields if provided
        if profile_data.full_name is not None:
            current_user.full_name = profile_data.full_name
        if profile_data.age is not None:
            current_user.age = profile_data.age
        if profile_data.guardian_contact is not None:
            current_user.guardian_contact = profile_data.guardian_contact
        if profile_data.guardian_email is not None:
            current_user.guardian_email = profile_data.guardian_email
        
        await db.commit()
        await db.refresh(current_user)
        
        logger.info(f"✅ Profile updated for user: {current_user.username}")
        
        return {"message": "Profile updated successfully"}
    except Exception as e:
        logger.error(f"❌ Profile update failed: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(request: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Refresh access token"""
    try:
        payload = jwt.decode(request.refresh_token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id_str: str = payload.get("sub")
        
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user_id = int(user_id_str)
        
        # Get user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Create new tokens
        if user.token_version is None:
            user.token_version = 1
            await db.commit()

        access_token = create_access_token(data={
            "sub": str(user.id),
            "token_version": user.token_version or 1,
            "jti": str(uuid4()),
        })
        new_refresh_token = create_refresh_token(data={
            "sub": str(user.id),
            "token_version": user.token_version or 1,
            "jti": str(uuid4()),
        })
        
        # Check if email verification is required
        email_verified = getattr(user, 'email_verified', True)
        
        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            requires_assessment=not user.has_completed_initial_assessment
        )
        
    except (JWTError, ValueError, TypeError) as e:
        logger.error(f"❌ Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
