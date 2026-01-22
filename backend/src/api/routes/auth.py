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
import logging
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from src.models.database import get_db
from src.models.models import User
from src.utils.config import settings

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


class UserLogin(BaseModel):
    username: str
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class OTPVerification(BaseModel):
    email: str
    otp: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    requires_assessment: bool = False
    requires_email_verification: bool = False


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    age: Optional[int]
    has_completed_initial_assessment: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# In-memory OTP storage (use Redis in production)
otp_storage = {}


# Helper functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash password"""
    return pwd_context.hash(password)


def generate_otp() -> str:
    """Generate 6-digit OTP"""
    return ''.join([str(secrets.randbelow(10)) for _ in range(6)])


def send_otp_email(email: str, otp: str) -> bool:
    """Send OTP via email (mock implementation - configure SMTP in production)"""
    try:
        # Store OTP with expiration (5 minutes)
        otp_storage[email] = {
            'otp': otp,
            'expires_at': datetime.utcnow() + timedelta(minutes=5)
        }
        
        logger.info(f"📧 OTP for {email}: {otp} (Mock - configure SMTP for production)")
        
        # TODO: Configure SMTP settings in production
        # smtp_server = settings.SMTP_SERVER
        # smtp_port = settings.SMTP_PORT
        # smtp_user = settings.SMTP_USER
        # smtp_password = settings.SMTP_PASSWORD
        # 
        # message = MIMEMultipart()
        # message['From'] = smtp_user
        # message['To'] = email
        # message['Subject'] = 'NeuroWell - Email Verification OTP'
        # 
        # body = f"Your verification code is: {otp}\n\nThis code expires in 5 minutes."
        # message.attach(MIMEText(body, 'plain'))
        # 
        # with smtplib.SMTP(smtp_server, smtp_port) as server:
        #     server.starttls()
        #     server.login(smtp_user, smtp_password)
        #     server.send_message(message)
        
        return True
    except Exception as e:
        logger.error(f"❌ Failed to send OTP: {e}")
        return False


def verify_otp(email: str, otp: str) -> bool:
    """Verify OTP for email"""
    if email not in otp_storage:
        return False
    
    stored_data = otp_storage[email]
    
    # Check if OTP expired
    if datetime.utcnow() > stored_data['expires_at']:
        del otp_storage[email]
        return False
    
    # Verify OTP
    if stored_data['otp'] == otp:
        del otp_storage[email]  # Remove after successful verification
        return True
    
    return False


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
    
    return user


# Routes
@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    """Register new user and send OTP for verification"""
    try:
        # Check if username exists
        result = await db.execute(select(User).where(User.username == user_data.username))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        
        # Check if email exists
        result = await db.execute(select(User).where(User.email == user_data.email))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
        
        # Generate and send OTP
        otp = generate_otp()
        if not send_otp_email(user_data.email, otp):
            logger.warning(f"⚠️ OTP sending failed for: {user_data.email}")
        
        logger.info(f"✅ OTP sent to {user_data.email}: {otp}")
        
        # Store user data temporarily (will be created after OTP verification)
        otp_storage[user_data.email]['user_data'] = user_data.dict()
        
        return {
            "message": "OTP sent to your email. Please verify to complete registration.",
            "email": user_data.email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/verify-otp", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def verify_otp_and_create_user(verification: OTPVerification, db: AsyncSession = Depends(get_db)):
    """Verify OTP and create user account"""
    try:
        if not verify_otp(verification.email, verification.otp):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP"
            )
        
        # Get stored user data
        if verification.email not in otp_storage or 'user_data' not in otp_storage[verification.email]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration session expired. Please register again."
            )
        
        user_data_dict = otp_storage[verification.email]['user_data']
        del otp_storage[verification.email]  # Clean up
        
        # Create new user
        new_user = User(
            username=user_data_dict['username'],
            email=user_data_dict['email'],
            password_hash=get_password_hash(user_data_dict['password']),
            full_name=user_data_dict.get('full_name'),
            age=user_data_dict.get('age'),
            guardian_contact=user_data_dict.get('guardian_contact'),
            has_completed_initial_assessment=False,
            email_verified=True
        )
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        logger.info(f"✅ New user created after OTP verification: {new_user.username}")
        
        return new_user
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ OTP verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Verification failed"
        )


@router.post("/resend-otp")
async def resend_otp(email: EmailStr, db: AsyncSession = Depends(get_db)):
    """Resend OTP to email"""
    try:
        # Check if email has pending registration
        if email not in otp_storage or 'user_data' not in otp_storage[email]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No pending registration for this email"
            )
        
        # Generate new OTP
        otp = generate_otp()
        if not send_otp_email(email, otp):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send OTP"
            )
        
        logger.info(f"✅ OTP resent to {email}: {otp}")
        
        return {"message": "OTP sent successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Resend OTP failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend OTP"
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
        user.last_login = datetime.utcnow()
        await db.commit()
        
        # Create tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        logger.info(f"✅ User logged in: {user.username}")
        
        # Check if email verification is required
        email_verified = getattr(user, 'email_verified', True)  # Default to True for backward compatibility
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            requires_assessment=not user.has_completed_initial_assessment,
            requires_email_verification=not email_verified
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
        access_token = create_access_token(data={"sub": str(user.id)})
        new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        # Check if email verification is required
        email_verified = getattr(user, 'email_verified', True)
        
        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            requires_assessment=not user.has_completed_initial_assessment,
            requires_email_verification=not email_verified
        )
        
    except (JWTError, ValueError, TypeError) as e:
        logger.error(f"❌ Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post("/verify-otp")
async def verify_email_otp(
    verification: OTPVerification,
    db: AsyncSession = Depends(get_db)
):
    """Verify email OTP"""
    try:
        # Verify OTP
        if not verify_otp(verification.email, verification.otp):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP"
            )
        
        # Find user and mark email as verified
        result = await db.execute(select(User).where(User.email == verification.email))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Mark email as verified
        if hasattr(user, 'email_verified'):
            user.email_verified = True
            await db.commit()
        
        logger.info(f"✅ Email verified for user: {user.username}")
        
        return {"message": "Email verified successfully", "email": verification.email}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Email verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed"
        )


@router.post("/resend-otp")
async def resend_otp(
    email: EmailStr,
    db: AsyncSession = Depends(get_db)
):
    """Resend OTP to email"""
    try:
        # Check if user exists
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if already verified
        if hasattr(user, 'email_verified') and user.email_verified:
            return {"message": "Email already verified", "email": email}
        
        # Generate and send new OTP
        otp = generate_otp()
        if not send_otp_email(email, otp):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send OTP"
            )
        
        logger.info(f"📧 OTP resent to: {email}")
        
        return {"message": "OTP sent successfully", "email": email}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ OTP resend failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend OTP"
        )
