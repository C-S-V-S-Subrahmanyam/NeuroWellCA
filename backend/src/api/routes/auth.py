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

from src.models.database import get_db
from src.models.models import User, Role
from src.utils.config import settings
from src.services.permission_service import PermissionService

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


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    requires_assessment: bool = False


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
    
    return user


# Routes
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    """Register new user (direct registration without OTP)"""
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
        
        # Create new user directly
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=get_password_hash(user_data.password),
            full_name=user_data.full_name,
            age=user_data.age,
            guardian_contact=user_data.guardian_contact,
            has_completed_initial_assessment=False,
            email_verified=True  # Auto-verified for now
        )
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        logger.info(f"✅ New user created: {new_user.username}")
        
        # Assign default "patient" role with full permissions
        try:
            result = await db.execute(select(Role).where(Role.code == "patient"))
            patient_role = result.scalar_one_or_none()
            
            if patient_role:
                await PermissionService.assign_role_to_user(
                    db=db,
                    user_id=new_user.id,
                    role_id=patient_role.id
                )
                logger.info(f"✅ Assigned 'patient' role to user: {new_user.username}")
            else:
                logger.warning(f"⚠️ 'patient' role not found in database")
        except Exception as perm_error:
            logger.error(f"❌ Failed to assign default role: {perm_error}")
            # Don't fail registration if permission assignment fails
        
        return new_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
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


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    age: Optional[int] = None
    guardian_contact: Optional[str] = None


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
        access_token = create_access_token(data={"sub": str(user.id)})
        new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
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
