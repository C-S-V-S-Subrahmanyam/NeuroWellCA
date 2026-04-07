"""
Admin Management Routes
User management, role assignments, and direct permission management
Database stats and monitoring
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, or_
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import httpx

from src.models.database import get_db
from src.models.models import (
    User, Assessment, Conversation, CrisisLog, ChatSession,
    Role, Permission, PermissionSet, UserRole, UserPermission, UserPermissionSet, LlmProvider
)
from src.api.dependencies import require_permission, get_current_user
from src.services.permission_service import PermissionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


# Pydantic models
class TableInfo(BaseModel):
    name: str
    row_count: int


class DatabaseStats(BaseModel):
    total_users: int
    total_conversations: int
    total_assessments: int
    total_crisis_logs: int
    total_sessions: int


class UserDetail(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    age: Optional[int]
    has_completed_initial_assessment: bool
    created_at: datetime
    last_login: Optional[datetime]


class ConversationDetail(BaseModel):
    id: int
    user_id: int
    session_id: str
    message_text: str
    sender: str
    crisis_detected: bool
    created_at: datetime


class AssessmentDetail(BaseModel):
    id: int
    user_id: int
    phq9_score: int
    gad7_score: int
    stress_level: int
    risk_level: str
    created_at: datetime


@router.get("/stats", response_model=DatabaseStats)
async def get_database_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get overall database statistics"""
    try:
        # Count users
        user_count = await db.execute(select(func.count(User.id)))
        total_users = user_count.scalar() or 0
        
        # Count conversations
        conv_count = await db.execute(select(func.count(Conversation.id)))
        total_conversations = conv_count.scalar() or 0
        
        # Count assessments
        assess_count = await db.execute(select(func.count(Assessment.id)))
        total_assessments = assess_count.scalar() or 0
        
        # Count crisis logs
        crisis_count = await db.execute(select(func.count(CrisisLog.id)))
        total_crisis_logs = crisis_count.scalar() or 0
        
        # Count sessions
        session_count = await db.execute(select(func.count(ChatSession.id)))
        total_sessions = session_count.scalar() or 0
        
        return DatabaseStats(
            total_users=total_users,
            total_conversations=total_conversations,
            total_assessments=total_assessments,
            total_crisis_logs=total_crisis_logs,
            total_sessions=total_sessions
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get database stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")


@router.get("/users", response_model=List[UserDetail])
async def get_all_users(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0)
):
    """Get all users (paginated)"""
    try:
        result = await db.execute(
            select(User)
            .order_by(User.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        users = result.scalars().all()
        
        return [
            UserDetail(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                age=user.age,
                has_completed_initial_assessment=user.has_completed_initial_assessment,
                created_at=user.created_at,
                last_login=user.last_login
            )
            for user in users
        ]
        
    except Exception as e:
        logger.error(f"❌ Failed to get users: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve users")


@router.get("/conversations", response_model=List[ConversationDetail])
async def get_all_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    user_id: Optional[int] = None,
    session_id: Optional[str] = None,
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get conversations with optional filters"""
    try:
        query = select(Conversation).order_by(Conversation.created_at.desc())
        
        if user_id:
            query = query.where(Conversation.user_id == user_id)
        
        if session_id:
            query = query.where(Conversation.session_id == session_id)
        
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        conversations = result.scalars().all()
        
        return [
            ConversationDetail(
                id=conv.id,
                user_id=conv.user_id,
                session_id=conv.session_id,
                message_text=conv.message_text,
                sender=conv.sender,
                crisis_detected=conv.crisis_detected or False,
                created_at=conv.created_at
            )
            for conv in conversations
        ]
        
    except Exception as e:
        logger.error(f"❌ Failed to get conversations: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve conversations")


@router.get("/assessments", response_model=List[AssessmentDetail])
async def get_all_assessments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    user_id: Optional[int] = None,
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get assessments with optional filters"""
    try:
        query = select(Assessment).order_by(Assessment.created_at.desc())
        
        if user_id:
            query = query.where(Assessment.user_id == user_id)
        
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        assessments = result.scalars().all()
        
        return [
            AssessmentDetail(
                id=assess.id,
                user_id=assess.user_id,
                phq9_score=assess.phq9_score,
                gad7_score=assess.gad7_score,
                stress_level=assess.stress_level,
                risk_level=assess.risk_level.value,
                created_at=assess.created_at
            )
            for assess in assessments
        ]
        
    except Exception as e:
        logger.error(f"❌ Failed to get assessments: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve assessments")


@router.get("/query", response_model=List[Dict[str, Any]])
async def execute_custom_query(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    query: str = Query(..., description="SQL SELECT query to execute")
):
    """Execute custom SQL query (SELECT only for safety)"""
    try:
        # Validate query is SELECT only
        query_lower = query.lower().strip()
        if not query_lower.startswith("select"):
            raise HTTPException(
                status_code=400,
                detail="Only SELECT queries are allowed"
            )
        
        # Execute query
        result = await db.execute(text(query))
        rows = result.fetchall()
        
        # Convert to dict
        columns = result.keys()
        data = [dict(zip(columns, row)) for row in rows]
        
        return data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Query execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.get("/tables", response_model=List[TableInfo])
async def get_table_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get information about all tables"""
    try:
        tables = [
            ("users", User),
            ("conversations", Conversation),
            ("assessments", Assessment),
            ("crisis_logs", CrisisLog),
            ("chat_sessions", ChatSession)
        ]
        
        table_info = []
        
        for table_name, model in tables:
            count_result = await db.execute(select(func.count()).select_from(model))
            row_count = count_result.scalar() or 0
            
            table_info.append(TableInfo(
                name=table_name,
                row_count=row_count
            ))
        
        return table_info
        
    except Exception as e:
        logger.error(f"❌ Failed to get table info: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve table information")


# ========== NEW RBAC USER MANAGEMENT ENDPOINTS ==========

class UserListResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    roles: List[str]


class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    age: Optional[int] = None
    guardian_contact: Optional[str] = None
    is_active: Optional[bool] = None
    email_verified: Optional[bool] = None


class RoleAssignment(BaseModel):
    role_id: int


class RoleListResponse(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str]
    is_system: bool
    assigned_at: Optional[datetime] = None


class PermissionResponse(BaseModel):
    id: int
    code: str
    name: str
    category: str


class EffectivePermissionsResponse(BaseModel):
    user_id: int
    username: str
    permissions: List[str]
    permission_count: int
    roles: List[str]
    direct_permissions: List[str]
    direct_permission_sets: List[str]


class LlmProviderAdminRequest(BaseModel):
    name: str
    provider_type: str
    model_name: str
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    is_active: bool = False
    is_default: bool = False


class LlmProviderAdminUpdate(BaseModel):
    name: Optional[str] = None
    provider_type: Optional[str] = None
    model_name: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class LlmProviderTestRequest(BaseModel):
    provider_type: str
    model_name: str
    base_url: Optional[str] = None
    api_key: Optional[str] = None


class LlmProviderReorderRequest(BaseModel):
    provider_ids: List[int]


def _provider_model_name(provider: LlmProvider) -> str:
    cfg = provider.config or {}
    if cfg.get("model"):
        return str(cfg.get("model"))
    if provider.models and len(provider.models) > 0:
        return str(provider.models[0])
    return ""


def _provider_fallback_order(provider: LlmProvider) -> int:
    cfg = provider.config or {}
    raw = cfg.get("fallback_order")
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 10_000


def _set_provider_fallback_order(provider: LlmProvider, order: int) -> None:
    cfg = dict(provider.config or {})
    cfg["fallback_order"] = int(order)
    provider.config = cfg


async def _run_provider_health_test(
    provider_type: str,
    model_name: str,
    base_url: Optional[str],
    api_key: Optional[str],
) -> Dict[str, Any]:
    normalized_type = (provider_type or "").strip().lower()
    model = (model_name or "").strip()
    key = (api_key or "").strip()
    url = (base_url or "").strip()

    if normalized_type in {"openai", "chatgpt", "deepseek", "custom"}:
        if not key:
            return {"success": False, "message": "API key is required for this provider."}
        resolved_url = url or ("https://api.deepseek.com/v1" if normalized_type == "deepseek" else "https://api.openai.com/v1")
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 5,
        }
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                started = datetime.now()
                response = await client.post(f"{resolved_url.rstrip('/')}/chat/completions", json=payload, headers=headers)
                elapsed = int((datetime.now() - started).total_seconds() * 1000)
            if response.status_code == 200:
                return {"success": True, "message": "Connection successful", "response_time_ms": elapsed}
            return {"success": False, "message": f"Provider returned {response.status_code}: {response.text[:220]}"}
        except Exception as exc:
            return {"success": False, "message": f"Connection failed: {exc}"}

    if normalized_type == "gemini":
        if not key:
            return {"success": False, "message": "API key is required for Gemini."}
        resolved_url = url or "https://generativelanguage.googleapis.com/v1beta"
        endpoint = f"{resolved_url.rstrip('/')}/models/{model}:generateContent"
        payload = {"contents": [{"parts": [{"text": "ping"}]}]}
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                started = datetime.now()
                response = await client.post(endpoint, params={"key": key}, json=payload)
                elapsed = int((datetime.now() - started).total_seconds() * 1000)
            if response.status_code == 200:
                return {"success": True, "message": "Connection successful", "response_time_ms": elapsed}
            return {"success": False, "message": f"Provider returned {response.status_code}: {response.text[:220]}"}
        except Exception as exc:
            return {"success": False, "message": f"Connection failed: {exc}"}

    if normalized_type == "ollama":
        resolved_url = url or "http://localhost:11434"
        payload = {
            "model": model,
            "prompt": "ping",
            "stream": False,
            "options": {"num_predict": 5},
        }
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                started = datetime.now()
                response = await client.post(f"{resolved_url.rstrip('/')}/api/generate", json=payload)
                elapsed = int((datetime.now() - started).total_seconds() * 1000)
            if response.status_code == 200:
                return {"success": True, "message": "Connection successful", "response_time_ms": elapsed}
            return {"success": False, "message": f"Provider returned {response.status_code}: {response.text[:220]}"}
        except Exception as exc:
            return {"success": False, "message": f"Connection failed: {exc}"}

    return {"success": False, "message": f"Unsupported provider_type '{provider_type}'"}


@router.get("/llm/providers")
async def list_admin_llm_providers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List configured providers for admin UI."""
    result = await db.execute(select(LlmProvider).where(LlmProvider.deleted_at == None))
    providers = result.scalars().all()

    sorted_providers = sorted(
        providers,
        key=lambda p: (
            0 if p.is_default else 1,
            _provider_fallback_order(p),
            0 if p.is_active else 1,
            (p.name or "").lower(),
        ),
    )

    return {
        "providers": [
            {
                "id": p.id,
                "name": p.name,
                "provider_type": p.provider_type,
                "model_name": _provider_model_name(p),
                "base_url": p.base_url,
                "has_api_key": bool((p.api_key_encrypted or "").strip()),
                "is_active": p.is_active,
                "is_default": p.is_default,
                "fallback_order": _provider_fallback_order(p),
                "updated_at": p.updated_at,
                "created_at": p.created_at,
            }
            for p in sorted_providers
        ]
    }


@router.get("/llm/active")
async def get_active_llm_provider(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current globally active provider; if none, chat falls back to Ollama."""
    result = await db.execute(
        select(LlmProvider)
        .where(LlmProvider.deleted_at == None, LlmProvider.is_active == True)
        .order_by(LlmProvider.updated_at.desc(), LlmProvider.id.desc())
    )
    provider = result.scalars().first()

    if not provider:
        return {
            "mode": "fallback_ollama",
            "active_provider": None,
            "message": "No active external provider. Chat uses Ollama fallback.",
        }

    cfg = provider.config or {}
    return {
        "mode": "provider",
        "active_provider": {
            "id": provider.id,
            "name": provider.name,
            "provider_type": provider.provider_type,
            "model_name": cfg.get("model") or (provider.models[0] if provider.models else ""),
            "has_api_key": bool((provider.api_key_encrypted or "").strip()),
            "updated_at": provider.updated_at,
        },
        "message": "All users currently chat through this provider.",
    }


@router.post("/llm/providers")
async def create_admin_llm_provider(
    payload: LlmProviderAdminRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a provider and optionally make it globally active."""
    provider_type = payload.provider_type.strip().lower()
    allowed = {"ollama", "openai", "chatgpt", "gemini", "deepseek", "custom"}
    if provider_type not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported provider_type. Use one of: {sorted(allowed)}")

    if payload.is_active:
        await db.execute(LlmProvider.__table__.update().values(is_active=False))
    if payload.is_default:
        await db.execute(LlmProvider.__table__.update().values(is_default=False))

    existing = await db.execute(select(LlmProvider).where(LlmProvider.deleted_at == None))
    existing_providers = existing.scalars().all()
    max_order = max([_provider_fallback_order(p) for p in existing_providers if not p.is_default] or [0])
    fallback_order = 0 if payload.is_default else max_order + 1

    provider = LlmProvider(
        name=payload.name.strip(),
        provider_type=provider_type,
        base_url=(payload.base_url or "").strip() or None,
        api_key_encrypted=(payload.api_key or "").strip(),
        config={"model": payload.model_name.strip(), "fallback_order": fallback_order},
        models=[payload.model_name.strip()],
        is_active=payload.is_active,
        is_default=payload.is_default,
        updated_at=datetime.now(),
    )
    db.add(provider)
    await db.commit()
    await db.refresh(provider)

    return {"message": "LLM provider created", "provider_id": provider.id}


@router.put("/llm/providers/{provider_id}")
async def update_admin_llm_provider(
    provider_id: int,
    payload: LlmProviderAdminUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update provider details and key from admin."""
    result = await db.execute(
        select(LlmProvider).where(LlmProvider.id == provider_id, LlmProvider.deleted_at == None)
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    if payload.is_active is True and not provider.is_active:
        await db.execute(LlmProvider.__table__.update().values(is_active=False))
    if payload.is_default is True and not provider.is_default:
        await db.execute(LlmProvider.__table__.update().values(is_default=False))

    if payload.name is not None:
        provider.name = payload.name.strip()
    if payload.provider_type is not None:
        provider.provider_type = payload.provider_type.strip().lower()
    if payload.base_url is not None:
        provider.base_url = payload.base_url.strip() or None
    if payload.api_key is not None:
        provider.api_key_encrypted = payload.api_key.strip()
    if payload.model_name is not None:
        provider.config = {**(provider.config or {}), "model": payload.model_name.strip()}
        provider.models = [payload.model_name.strip()]
    if payload.is_active is not None:
        provider.is_active = payload.is_active
    if payload.is_default is not None:
        provider.is_default = payload.is_default
        if payload.is_default:
            _set_provider_fallback_order(provider, 0)

    provider.updated_at = datetime.now()
    await db.commit()

    return {"message": "LLM provider updated"}


@router.post("/llm/providers/{provider_id}/activate")
async def activate_admin_llm_provider(
    provider_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Activate one provider globally for all users."""
    result = await db.execute(
        select(LlmProvider).where(LlmProvider.id == provider_id, LlmProvider.deleted_at == None)
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    provider_type = (provider.provider_type or "").strip().lower()
    requires_key = provider_type != "ollama"
    if requires_key and not (provider.api_key_encrypted or "").strip():
        raise HTTPException(
            status_code=400,
            detail="This provider requires an API key before activation.",
        )

    await db.execute(LlmProvider.__table__.update().values(is_active=False))
    provider.is_active = True
    provider.updated_at = datetime.now()
    await db.commit()

    return {
        "message": "Active LLM provider updated globally",
        "provider_id": provider.id,
        "provider_name": provider.name,
        "provider_type": provider.provider_type,
    }


@router.post("/llm/providers/{provider_id}/set-default")
async def set_default_admin_llm_provider(
    provider_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Pin selected provider as default at the top of fallback list."""
    result = await db.execute(
        select(LlmProvider).where(LlmProvider.id == provider_id, LlmProvider.deleted_at == None)
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    await db.execute(LlmProvider.__table__.update().values(is_default=False))
    provider.is_default = True
    _set_provider_fallback_order(provider, 0)
    provider.updated_at = datetime.now()
    await db.commit()

    return {"message": "Default provider updated", "provider_id": provider.id}


@router.post("/llm/providers/reorder")
async def reorder_admin_llm_providers(
    payload: LlmProviderReorderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reorder non-default fallback providers while keeping default provider at top."""
    result = await db.execute(select(LlmProvider).where(LlmProvider.deleted_at == None))
    providers = result.scalars().all()
    provider_map = {p.id: p for p in providers}

    non_default_ids = [p.id for p in providers if not p.is_default]
    seen = set()
    ordered_ids = []
    for pid in payload.provider_ids:
        if pid in non_default_ids and pid not in seen:
            ordered_ids.append(pid)
            seen.add(pid)
    for pid in non_default_ids:
        if pid not in seen:
            ordered_ids.append(pid)

    for idx, pid in enumerate(ordered_ids, start=1):
        provider = provider_map.get(pid)
        if provider:
            _set_provider_fallback_order(provider, idx)
            provider.updated_at = datetime.now()

    await db.commit()
    return {"message": "Fallback order updated"}


@router.post("/llm/providers/{provider_id}/test")
async def test_admin_llm_provider(
    provider_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Test stored API key/model/base URL for one configured provider."""
    result = await db.execute(
        select(LlmProvider).where(LlmProvider.id == provider_id, LlmProvider.deleted_at == None)
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    test_result = await _run_provider_health_test(
        provider_type=provider.provider_type,
        model_name=_provider_model_name(provider),
        base_url=provider.base_url,
        api_key=provider.api_key_encrypted,
    )

    provider.last_health_check = datetime.now()
    provider.health_status = "healthy" if test_result.get("success") else "unhealthy"
    provider.health_message = test_result.get("message")
    provider.updated_at = datetime.now()
    await db.commit()

    return {
        "provider_id": provider.id,
        "provider_name": provider.name,
        **test_result,
    }


@router.post("/llm/providers/test-config")
async def test_admin_llm_provider_config(
    payload: LlmProviderTestRequest,
    current_user: User = Depends(get_current_user),
):
    """Test a provider configuration before saving it."""
    test_result = await _run_provider_health_test(
        provider_type=payload.provider_type,
        model_name=payload.model_name,
        base_url=payload.base_url,
        api_key=payload.api_key,
    )
    return test_result


@router.delete("/llm/providers/{provider_id}")
async def delete_admin_llm_provider(
    provider_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete provider from admin. If active provider is removed, chat falls back to Ollama."""
    result = await db.execute(
        select(LlmProvider).where(LlmProvider.id == provider_id, LlmProvider.deleted_at == None)
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    provider.deleted_at = datetime.now()
    provider.is_active = False
    provider.is_default = False
    provider.updated_at = datetime.now()
    await db.commit()

    return {
        "message": "Provider deleted. If no active provider remains, chat uses Ollama fallback.",
        "provider_id": provider_id,
    }


@router.get("/rbac/users", response_model=dict)
async def list_rbac_users(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all users with RBAC info"""
    logger.info(f"👥 Listing RBAC users for admin {current_user.username}")
    query = select(User).where(User.deleted_at == None)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                User.username.ilike(search_pattern),
                User.email.ilike(search_pattern),
                User.full_name.ilike(search_pattern)
            )
        )
    
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar()
    
    query = query.options(selectinload(User.user_roles).selectinload(UserRole.role))
    query = query.offset(offset).limit(limit).order_by(User.created_at.desc())
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    users_data = []
    for user in users:
        roles = [ur.role.name for ur in user.user_roles if ur.role.is_active and not ur.role.deleted_at]
        users_data.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "last_login": user.last_login,
            "roles": roles
        })
    
    return {
        "users": users_data,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total
    }


@router.put("/rbac/users/{user_id}")
async def update_rbac_user(
    user_id: int,
    user_update: UserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user information"""
    logger.info(f"✏️ Updating user {user_id} by admin {current_user.username}")
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at == None)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    user.updated_at = datetime.now()
    await db.commit()
    await db.refresh(user)
    
    return {"message": "User updated successfully", "user_id": user_id}


@router.delete("/rbac/users/{user_id}")
async def delete_rbac_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Soft delete a user"""
    logger.info(f"🗑️ Deleting user {user_id} by admin {current_user.username}")
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at == None)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.deleted_at = datetime.now()
    user.is_active = False
    await db.commit()
    
    return {"message": "User deleted successfully"}


@router.get("/rbac/users/{user_id}/roles", response_model=List[RoleListResponse])
async def get_user_roles_rbac(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all roles assigned to a user"""
    logger.info(f"🎭 Getting roles for user {user_id} by admin {current_user.username}")
    roles = await PermissionService.get_user_roles(db, user_id)
    return roles


@router.post("/rbac/users/{user_id}/roles")
async def assign_role_rbac(
    user_id: int,
    role_assignment: RoleAssignment,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign a role to a user"""
    logger.info(f"➕ Assigning role to user {user_id} by admin {current_user.username}")
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at == None)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = await db.execute(
        select(Role).where(Role.id == role_assignment.role_id, Role.deleted_at == None)
    )
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    success = await PermissionService.assign_role_to_user(
        db, user_id, role_assignment.role_id, current_user.id
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to assign role")
    
    return {"message": f"Role '{role.name}' assigned successfully"}


@router.delete("/rbac/users/{user_id}/roles/{role_id}")
async def remove_role_rbac(
    user_id: int,
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a role from a user"""
    logger.info(f"➖ Removing role {role_id} from user {user_id} by admin {current_user.username}")
    success = await PermissionService.remove_role_from_user(
        db, user_id, role_id, current_user.id
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to remove role")
    
    return {"message": "Role removed successfully"}


@router.get("/rbac/users/{user_id}/permissions/effective", response_model=EffectivePermissionsResponse)
async def get_effective_permissions_rbac(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all effective permissions for a user"""
    logger.info(f"🔐 Getting effective permissions for user {user_id} by admin {current_user.username}")
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at == None)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    permissions = await PermissionService.get_user_permissions(db, user_id)
    roles = await PermissionService.get_user_roles(db, user_id)
    role_names = [r["name"] for r in roles]
    
    result = await db.execute(
        select(UserPermission)
        .options(selectinload(UserPermission.permission))
        .where(UserPermission.user_id == user_id)
    )
    direct_perms = result.scalars().all()
    direct_perm_codes = [up.permission.code for up in direct_perms if up.permission.is_active]
    
    result = await db.execute(
        select(UserPermissionSet)
        .options(selectinload(UserPermissionSet.permission_set))
        .where(UserPermissionSet.user_id == user_id)
    )
    direct_sets = result.scalars().all()
    direct_set_codes = [ups.permission_set.code for ups in direct_sets if ups.permission_set.is_active]
    
    return {
        "user_id": user_id,
        "username": user.username,
        "permissions": sorted(list(permissions)),
        "permission_count": len(permissions),
        "roles": role_names,
        "direct_permissions": direct_perm_codes,
        "direct_permission_sets": direct_set_codes
    }
