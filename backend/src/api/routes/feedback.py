"""
Feedback System Endpoints
Mental Health Chatbot - Message feedback and golden examples management
"""

from typing import List, Optional, Dict
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field
import logging

from src.models.database import get_db
from src.models.models import User, MessageFeedback, GoldenExample
from src.api.dependencies import get_current_user, require_permission, require_any_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feedback", tags=["feedback"])

# ========== PYDANTIC MODELS ==========

class FeedbackSubmit(BaseModel):
    message_id: str
    conversation_id: int
    feedback_type: str = Field(..., pattern="^(positive|negative|flag)$")
    reason: Optional[str] = None
    details: Optional[str] = None
    suggested_response: Optional[str] = None

class FeedbackResponse(BaseModel):
    id: int
    user_id: int
    username: str
    message_id: str
    conversation_id: int
    feedback_type: str
    reason: Optional[str]
    details: Optional[str]
    suggested_response: Optional[str]
    status: str
    admin_notes: Optional[str]
    created_at: datetime
    updated_at: datetime

class FeedbackUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(pending|reviewed|resolved|dismissed)$")
    admin_notes: Optional[str] = None

class GoldenExampleCreate(BaseModel):
    message_id: Optional[str] = None
    user_input: str
    ai_response: str
    scenario_type: str
    tags: Optional[List[str]] = []
    notes: Optional[str] = None

class GoldenExampleResponse(BaseModel):
    id: int
    message_id: Optional[str]
    user_input: str
    ai_response: str
    scenario_type: str
    tags: List[str]
    notes: Optional[str]
    created_by: int
    creator_username: str
    usage_count: int
    is_active: bool
    created_at: datetime


# ========== USER FEEDBACK ENDPOINTS ==========

@router.post("/submit")
async def submit_feedback(
    feedback: FeedbackSubmit,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit feedback on an AI message"""
    # Check if feedback already exists for this message
    result = await db.execute(
        select(MessageFeedback).where(
            MessageFeedback.user_id == current_user.id,
            MessageFeedback.message_id == feedback.message_id,
            MessageFeedback.deleted_at == None
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        # Update existing feedback
        existing.feedback_type = feedback.feedback_type
        existing.reason = feedback.reason
        existing.details = feedback.details
        existing.suggested_response = feedback.suggested_response
        existing.updated_at = datetime.now()
        await db.commit()
        return {"message": "Feedback updated", "id": existing.id}
    
    # Create new feedback
    new_feedback = MessageFeedback(
        user_id=current_user.id,
        message_id=feedback.message_id,
        conversation_id=feedback.conversation_id,
        feedback_type=feedback.feedback_type,
        reason=feedback.reason,
        details=feedback.details,
        suggested_response=feedback.suggested_response,
        status="pending"
    )
    db.add(new_feedback)
    await db.commit()
    await db.refresh(new_feedback)
    
    logger.info(f"✅ Feedback submitted by user {current_user.id} on message {feedback.message_id}")
    
    return {"message": "Feedback submitted successfully", "id": new_feedback.id}


@router.get("/my-feedback", response_model=List[FeedbackResponse])
async def get_my_feedback(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    feedback_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all feedback submitted by the current user"""
    query = select(MessageFeedback).where(
        MessageFeedback.user_id == current_user.id,
        MessageFeedback.deleted_at == None
    )
    
    if feedback_type:
        query = query.where(MessageFeedback.feedback_type == feedback_type)
    
    query = query.options(selectinload(MessageFeedback.user))
    query = query.order_by(MessageFeedback.created_at.desc())
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    feedbacks = result.scalars().all()
    
    return [
        {
            "id": f.id,
            "user_id": f.user_id,
            "username": f.user.username,
            "message_id": f.message_id,
            "conversation_id": f.conversation_id,
            "feedback_type": f.feedback_type,
            "reason": f.reason,
            "details": f.details,
            "suggested_response": f.suggested_response,
            "status": f.status,
            "admin_notes": f.admin_notes,
            "created_at": f.created_at,
            "updated_at": f.updated_at
        }
        for f in feedbacks
    ]


# ========== ADMIN FEEDBACK MANAGEMENT ==========

@router.get("/all", dependencies=[Depends(require_any_permission("feedback.view", "feedback.manage"))])
async def list_all_feedback(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    feedback_type: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all feedback (admin only)"""
    query = select(MessageFeedback).where(MessageFeedback.deleted_at == None)
    
    if feedback_type:
        query = query.where(MessageFeedback.feedback_type == feedback_type)
    if status:
        query = query.where(MessageFeedback.status == status)
    
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar()
    
    query = query.options(selectinload(MessageFeedback.user))
    query = query.order_by(MessageFeedback.created_at.desc())
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    feedbacks = result.scalars().all()
    
    feedback_data = [
        {
            "id": f.id,
            "user_id": f.user_id,
            "username": f.user.username,
            "message_id": f.message_id,
            "conversation_id": f.conversation_id,
            "feedback_type": f.feedback_type,
            "reason": f.reason,
            "details": f.details,
            "suggested_response": f.suggested_response,
            "status": f.status,
            "admin_notes": f.admin_notes,
            "created_at": f.created_at,
            "updated_at": f.updated_at
        }
        for f in feedbacks
    ]
    
    return {
        "feedbacks": feedback_data,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total
    }


@router.put("/{feedback_id}", dependencies=[Depends(require_permission("feedback.manage"))])
async def update_feedback(
    feedback_id: int,
    update: FeedbackUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update feedback status and admin notes"""
    result = await db.execute(
        select(MessageFeedback).where(
            MessageFeedback.id == feedback_id,
            MessageFeedback.deleted_at == None
        )
    )
    feedback = result.scalar_one_or_none()
    
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    if update.status:
        feedback.status = update.status
    if update.admin_notes is not None:
        feedback.admin_notes = update.admin_notes
    
    feedback.updated_at = datetime.now()
    await db.commit()
    
    logger.info(f"✅ Feedback {feedback_id} updated by admin {current_user.id}")
    
    return {"message": "Feedback updated successfully"}


@router.get("/stats", dependencies=[Depends(require_any_permission("feedback.view", "feedback.manage"))])
async def get_feedback_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get feedback statistics"""
    # Total feedback
    result = await db.execute(
        select(func.count()).select_from(MessageFeedback)
        .where(MessageFeedback.deleted_at == None)
    )
    total = result.scalar()
    
    # By type
    result = await db.execute(
        select(MessageFeedback.feedback_type, func.count())
        .where(MessageFeedback.deleted_at == None)
        .group_by(MessageFeedback.feedback_type)
    )
    by_type = {row[0]: row[1] for row in result.all()}
    
    # By status
    result = await db.execute(
        select(MessageFeedback.status, func.count())
        .where(MessageFeedback.deleted_at == None)
        .group_by(MessageFeedback.status)
    )
    by_status = {row[0]: row[1] for row in result.all()}
    
    return {
        "total_feedback": total,
        "by_type": by_type,
        "by_status": by_status,
        "pending_count": by_status.get("pending", 0)
    }


# ========== GOLDEN EXAMPLES MANAGEMENT ==========

@router.post("/golden-examples", dependencies=[Depends(require_permission("feedback.manage"))])
async def create_golden_example(
    example: GoldenExampleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a golden example from feedback or manually"""
    new_example = GoldenExample(
        message_id=example.message_id,
        user_input=example.user_input,
        ai_response=example.ai_response,
        scenario_type=example.scenario_type,
        tags=example.tags or [],
        notes=example.notes,
        created_by=current_user.id
    )
    db.add(new_example)
    await db.commit()
    await db.refresh(new_example)
    
    logger.info(f"✅ Golden example created by user {current_user.id}")
    
    return {"message": "Golden example created", "id": new_example.id}


@router.get("/golden-examples", dependencies=[Depends(require_any_permission("feedback.view", "ai.manage"))])
async def list_golden_examples(
    scenario_type: Optional[str] = None,
    tag: Optional[str] = None,
    is_active: bool = True,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List golden examples for training"""
    query = select(GoldenExample).where(GoldenExample.deleted_at == None)
    
    if is_active is not None:
        query = query.where(GoldenExample.is_active == is_active)
    if scenario_type:
        query = query.where(GoldenExample.scenario_type == scenario_type)
    if tag:
        query = query.where(GoldenExample.tags.contains([tag]))
    
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar()
    
    query = query.options(selectinload(GoldenExample.creator))
    query = query.order_by(GoldenExample.created_at.desc())
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    examples = result.scalars().all()
    
    examples_data = [
        {
            "id": ex.id,
            "message_id": ex.message_id,
            "user_input": ex.user_input,
            "ai_response": ex.ai_response,
            "scenario_type": ex.scenario_type,
            "tags": ex.tags,
            "notes": ex.notes,
            "created_by": ex.created_by,
            "creator_username": ex.creator.username if ex.creator else "Unknown",
            "usage_count": ex.usage_count,
            "is_active": ex.is_active,
            "created_at": ex.created_at
        }
        for ex in examples
    ]
    
    return {
        "examples": examples_data,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total
    }


@router.get("/golden-examples/{example_id}", dependencies=[Depends(require_any_permission("feedback.view", "ai.manage"))])
async def get_golden_example(
    example_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific golden example"""
    result = await db.execute(
        select(GoldenExample)
        .options(selectinload(GoldenExample.creator))
        .where(GoldenExample.id == example_id, GoldenExample.deleted_at == None)
    )
    example = result.scalar_one_or_none()
    
    if not example:
        raise HTTPException(status_code=404, detail="Golden example not found")
    
    return {
        "id": example.id,
        "message_id": example.message_id,
        "user_input": example.user_input,
        "ai_response": example.ai_response,
        "scenario_type": example.scenario_type,
        "tags": example.tags,
        "notes": example.notes,
        "created_by": example.created_by,
        "creator_username": example.creator.username if example.creator else "Unknown",
        "usage_count": example.usage_count,
        "is_active": example.is_active,
        "created_at": example.created_at
    }


@router.put("/golden-examples/{example_id}", dependencies=[Depends(require_permission("feedback.manage"))])
async def update_golden_example(
    example_id: int,
    is_active: Optional[bool] = None,
    notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update golden example status or notes"""
    result = await db.execute(
        select(GoldenExample).where(
            GoldenExample.id == example_id,
            GoldenExample.deleted_at == None
        )
    )
    example = result.scalar_one_or_none()
    
    if not example:
        raise HTTPException(status_code=404, detail="Golden example not found")
    
    if is_active is not None:
        example.is_active = is_active
    if notes is not None:
        example.notes = notes
    
    example.updated_at = datetime.now()
    await db.commit()
    
    return {"message": "Golden example updated"}


@router.delete("/golden-examples/{example_id}", dependencies=[Depends(require_permission("feedback.manage"))])
async def delete_golden_example(
    example_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Soft delete a golden example"""
    result = await db.execute(
        select(GoldenExample).where(
            GoldenExample.id == example_id,
            GoldenExample.deleted_at == None
        )
    )
    example = result.scalar_one_or_none()
    
    if not example:
        raise HTTPException(status_code=404, detail="Golden example not found")
    
    example.deleted_at = datetime.now()
    await db.commit()
    
    return {"message": "Golden example deleted"}


@router.post("/golden-examples/{example_id}/increment-usage", dependencies=[Depends(require_any_permission("ai.manage", "feedback.view"))])
async def increment_example_usage(
    example_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Increment usage counter when example is used in training"""
    result = await db.execute(
        select(GoldenExample).where(
            GoldenExample.id == example_id,
            GoldenExample.deleted_at == None
        )
    )
    example = result.scalar_one_or_none()
    
    if not example:
        raise HTTPException(status_code=404, detail="Golden example not found")
    
    example.usage_count += 1
    await db.commit()
    
    return {"message": "Usage count incremented", "usage_count": example.usage_count}
