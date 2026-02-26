"""
LLM Provider Management Endpoints
Mental Health Chatbot - Multi-LLM provider configuration and model discovery
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field
import logging
import httpx

from src.models.database import get_db
from src.models.models import User, LlmProvider
from src.api.dependencies import get_current_user, require_permission
from src.services.permission_service import PermissionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/llm-providers", tags=["llm-providers"])

# ========== PYDANTIC MODELS ==========

class LlmProviderCreate(BaseModel):
    name: str
    provider_type: str = Field(..., pattern="^(openai|anthropic|azure|local|custom)$")
    api_key: Optional[str] = None
    api_endpoint: Optional[str] = None
    model_name: str
    parameters: Optional[Dict[str, Any]] = {}
    is_default: bool = False

class LlmProviderUpdate(BaseModel):
    name: Optional[str] = None
    api_key: Optional[str] = None
    api_endpoint: Optional[str] = None
    model_name: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None

class LlmProviderResponse(BaseModel):
    id: int
    name: str
    provider_type: str
    api_endpoint: Optional[str]
    model_name: str
    parameters: Dict[str, Any]
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime]
    total_requests: int
    total_tokens: int

class ConnectionTestResult(BaseModel):
    success: bool
    provider_id: int
    provider_name: str
    model: str
    message: str
    response_time_ms: Optional[int] = None
    available_models: Optional[List[str]] = None


# ========== HELPER FUNCTIONS ==========

async def test_openai_connection(api_key: str, api_endpoint: str, model: str) -> Dict[str, Any]:
    """Test OpenAI API connection"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "test"}],
        "max_tokens": 5
    }
    
    endpoint = api_endpoint if api_endpoint else "https://api.openai.com/v1"
    
    try:
        async with httpx.AsyncClient() as client:
            start = datetime.now()
            response = await client.post(
                f"{endpoint}/chat/completions",
                json=payload,
                headers=headers,
                timeout=10.0
            )
            response_time = int((datetime.now() - start).total_seconds() * 1000)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Connection successful",
                    "response_time_ms": response_time
                }
            else:
                return {
                    "success": False,
                    "message": f"API error: {response.status_code} - {response.text}"
                }
    except Exception as e:
        return {
            "success": False,
            "message": f"Connection failed: {str(e)}"
        }


async def test_anthropic_connection(api_key: str, api_endpoint: str, model: str) -> Dict[str, Any]:
    """Test Anthropic API connection"""
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01"
    }
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "test"}],
        "max_tokens": 5
    }
    
    endpoint = api_endpoint if api_endpoint else "https://api.anthropic.com/v1"
    
    try:
        async with httpx.AsyncClient() as client:
            start = datetime.now()
            response = await client.post(
                f"{endpoint}/messages",
                json=payload,
                headers=headers,
                timeout=10.0
            )
            response_time = int((datetime.now() - start).total_seconds() * 1000)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Connection successful",
                    "response_time_ms": response_time
                }
            else:
                return {
                    "success": False,
                    "message": f"API error: {response.status_code} - {response.text}"
                }
    except Exception as e:
        return {
            "success": False,
            "message": f"Connection failed: {str(e)}"
        }


async def discover_openai_models(api_key: str, api_endpoint: str) -> List[str]:
    """Discover available OpenAI models"""
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    endpoint = api_endpoint if api_endpoint else "https://api.openai.com/v1"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{endpoint}/models",
                headers=headers,
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                models = [model["id"] for model in data.get("data", [])]
                # Filter to only chat models
                chat_models = [m for m in models if "gpt" in m.lower()]
                return sorted(chat_models)
            return []
    except:
        return []


# ========== LLM PROVIDER CRUD ENDPOINTS ==========

@router.get("/", dependencies=[Depends(require_permission("ai.view"))])
async def list_llm_providers(
    is_active: Optional[bool] = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all LLM providers"""
    query = select(LlmProvider).where(LlmProvider.deleted_at == None)
    
    if is_active is not None:
        query = query.where(LlmProvider.is_active == is_active)
    
    query = query.order_by(LlmProvider.is_default.desc(), LlmProvider.name)
    result = await db.execute(query)
    providers = result.scalars().all()
    
    return {
        "providers": [
            {
                "id": p.id,
                "name": p.name,
                "provider_type": p.provider_type,
                "api_endpoint": p.api_endpoint,
                "model_name": p.model_name,
                "parameters": p.parameters,
                "is_active": p.is_active,
                "is_default": p.is_default,
                "created_at": p.created_at,
                "updated_at": p.updated_at,
                "last_used_at": p.last_used_at,
                "total_requests": p.total_requests,
                "total_tokens": p.total_tokens
            }
            for p in providers
        ]
    }


@router.get("/{provider_id}", dependencies=[Depends(require_permission("ai.view"))])
async def get_llm_provider(
    provider_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific LLM provider"""
    result = await db.execute(
        select(LlmProvider).where(
            LlmProvider.id == provider_id,
            LlmProvider.deleted_at == None
        )
    )
    provider = result.scalar_one_or_none()
    
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    return {
        "id": provider.id,
        "name": provider.name,
        "provider_type": provider.provider_type,
        "api_endpoint": provider.api_endpoint,
        "model_name": provider.model_name,
        "parameters": provider.parameters,
        "is_active": provider.is_active,
        "is_default": provider.is_default,
        "created_at": provider.created_at,
        "updated_at": provider.updated_at,
        "last_used_at": provider.last_used_at,
        "total_requests": provider.total_requests,
        "total_tokens": provider.total_tokens
    }


@router.post("/", dependencies=[Depends(require_permission("ai.manage"))])
async def create_llm_provider(
    provider: LlmProviderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new LLM provider"""
    # If setting as default, unset other defaults
    if provider.is_default:
        await db.execute(
            LlmProvider.__table__.update()
            .where(LlmProvider.provider_type == provider.provider_type)
            .values(is_default=False)
        )
    
    new_provider = LlmProvider(
        name=provider.name,
        provider_type=provider.provider_type,
        api_key=provider.api_key,
        api_endpoint=provider.api_endpoint,
        model_name=provider.model_name,
        parameters=provider.parameters or {},
        is_default=provider.is_default,
        created_by=current_user.id
    )
    db.add(new_provider)
    await db.commit()
    await db.refresh(new_provider)
    
    await PermissionService.log_rbac_change(
        db, current_user.id, "llm_provider", "create",
        f"Created LLM provider {new_provider.name}", new_provider.id
    )
    
    logger.info(f"✅ LLM provider '{provider.name}' created by user {current_user.id}")
    
    return {"message": "LLM provider created", "id": new_provider.id}


@router.put("/{provider_id}", dependencies=[Depends(require_permission("ai.manage"))])
async def update_llm_provider(
    provider_id: int,
    update: LlmProviderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an LLM provider"""
    result = await db.execute(
        select(LlmProvider).where(
            LlmProvider.id == provider_id,
            LlmProvider.deleted_at == None
        )
    )
    provider = result.scalar_one_or_none()
    
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    # If setting as default, unset other defaults of same type
    if update.is_default and not provider.is_default:
        await db.execute(
            LlmProvider.__table__.update()
            .where(LlmProvider.provider_type == provider.provider_type)
            .values(is_default=False)
        )
    
    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(provider, field, value)
    
    provider.updated_at = datetime.now()
    await db.commit()
    
    await PermissionService.log_rbac_change(
        db, current_user.id, "llm_provider", "update",
        f"Updated LLM provider {provider.name}", provider_id
    )
    
    return {"message": "LLM provider updated"}


@router.delete("/{provider_id}", dependencies=[Depends(require_permission("ai.manage"))])
async def delete_llm_provider(
    provider_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Soft delete an LLM provider"""
    result = await db.execute(
        select(LlmProvider).where(
            LlmProvider.id == provider_id,
            LlmProvider.deleted_at == None
        )
    )
    provider = result.scalar_one_or_none()
    
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    if provider.is_default:
        raise HTTPException(status_code=400, detail="Cannot delete default provider. Set another provider as default first.")
    
    provider.deleted_at = datetime.now()
    provider.is_active = False
    await db.commit()
    
    await PermissionService.log_rbac_change(
        db, current_user.id, "llm_provider", "delete",
        f"Deleted LLM provider {provider.name}", provider_id
    )
    
    return {"message": "LLM provider deleted"}


# ========== CONNECTION TESTING ==========

@router.post("/{provider_id}/test", dependencies=[Depends(require_permission("ai.manage"))])
async def test_llm_connection(
    provider_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Test connection to an LLM provider"""
    result = await db.execute(
        select(LlmProvider).where(
            LlmProvider.id == provider_id,
            LlmProvider.deleted_at == None
        )
    )
    provider = result.scalar_one_or_none()
    
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    if not provider.api_key:
        raise HTTPException(status_code=400, detail="API key not configured")
    
    # Test based on provider type
    if provider.provider_type == "openai":
        test_result = await test_openai_connection(
            provider.api_key,
            provider.api_endpoint or "https://api.openai.com/v1",
            provider.model_name
        )
    elif provider.provider_type == "anthropic":
        test_result = await test_anthropic_connection(
            provider.api_key,
            provider.api_endpoint or "https://api.anthropic.com/v1",
            provider.model_name
        )
    elif provider.provider_type == "azure":
        # Azure OpenAI uses similar format
        test_result = await test_openai_connection(
            provider.api_key,
            provider.api_endpoint,
            provider.model_name
        )
    else:
        raise HTTPException(status_code=400, detail=f"Testing not supported for provider type: {provider.provider_type}")
    
    return {
        "success": test_result["success"],
        "provider_id": provider_id,
        "provider_name": provider.name,
        "model": provider.model_name,
        "message": test_result["message"],
        "response_time_ms": test_result.get("response_time_ms")
    }


@router.post("/{provider_id}/discover-models", dependencies=[Depends(require_permission("ai.manage"))])
async def discover_models(
    provider_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Discover available models from LLM provider"""
    result = await db.execute(
        select(LlmProvider).where(
            LlmProvider.id == provider_id,
            LlmProvider.deleted_at == None
        )
    )
    provider = result.scalar_one_or_none()
    
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    if not provider.api_key:
        raise HTTPException(status_code=400, detail="API key not configured")
    
    if provider.provider_type == "openai":
        models = await discover_openai_models(
            provider.api_key,
            provider.api_endpoint or "https://api.openai.com/v1"
        )
        return {
            "provider_id": provider_id,
            "provider_name": provider.name,
            "available_models": models,
            "count": len(models)
        }
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Model discovery not supported for provider type: {provider.provider_type}"
        )


@router.get("/stats/usage", dependencies=[Depends(require_permission("ai.view"))])
async def get_usage_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get usage statistics for all LLM providers"""
    result = await db.execute(
        select(LlmProvider).where(LlmProvider.deleted_at == None)
    )
    providers = result.scalars().all()
    
    stats = []
    total_requests = 0
    total_tokens = 0
    
    for provider in providers:
        stats.append({
            "provider_id": provider.id,
            "provider_name": provider.name,
            "provider_type": provider.provider_type,
            "total_requests": provider.total_requests,
            "total_tokens": provider.total_tokens,
            "last_used_at": provider.last_used_at
        })
        total_requests += provider.total_requests
        total_tokens += provider.total_tokens
    
    return {
        "providers": stats,
        "total_requests": total_requests,
        "total_tokens": total_tokens
    }
