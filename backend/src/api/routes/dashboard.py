"""
Dashboard routes for user analytics
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from src.models.database import get_db
from src.models.models import User, Assessment, Conversation, CrisisLog
from src.api.routes.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models
class DashboardStats(BaseModel):
    total_conversations: int
    total_assessments: int
    current_risk_level: Optional[str]
    recent_activity_days: int
    crisis_alerts: int


class AssessmentTrend(BaseModel):
    date: str
    phq9_score: int
    gad7_score: int
    stress_level: int
    risk_level: str


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard statistics"""
    try:
        # Total conversations
        conv_result = await db.execute(
            select(func.count(Conversation.id))
            .where(Conversation.user_id == current_user.id)
        )
        total_conversations = conv_result.scalar() or 0
        
        # Total assessments
        assess_result = await db.execute(
            select(func.count(Assessment.id))
            .where(Assessment.user_id == current_user.id)
        )
        total_assessments = assess_result.scalar() or 0
        
        # Current risk level (latest assessment)
        latest_assess_result = await db.execute(
            select(Assessment)
            .where(Assessment.user_id == current_user.id)
            .order_by(Assessment.created_at.desc())
            .limit(1)
        )
        latest_assessment = latest_assess_result.scalar_one_or_none()
        current_risk_level = latest_assessment.risk_level.value if latest_assessment else None
        
        # Recent activity (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        activity_result = await db.execute(
            select(func.count(Conversation.id))
            .where(Conversation.user_id == current_user.id)
            .where(Conversation.created_at >= seven_days_ago)
        )
        recent_activity = activity_result.scalar() or 0
        
        # Crisis alerts
        crisis_result = await db.execute(
            select(func.count(CrisisLog.id))
            .where(CrisisLog.user_id == current_user.id)
        )
        crisis_alerts = crisis_result.scalar() or 0
        
        return DashboardStats(
            total_conversations=total_conversations,
            total_assessments=total_assessments,
            current_risk_level=current_risk_level,
            recent_activity_days=7 if recent_activity > 0 else 0,
            crisis_alerts=crisis_alerts
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get dashboard stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")


@router.get("/trends", response_model=List[AssessmentTrend])
async def get_assessment_trends(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get assessment trends over time"""
    try:
        result = await db.execute(
            select(Assessment)
            .where(Assessment.user_id == current_user.id)
            .order_by(Assessment.created_at.desc())
            .limit(10)
        )
        assessments = result.scalars().all()
        
        trends = [
            AssessmentTrend(
                date=assess.created_at.strftime("%Y-%m-%d"),
                phq9_score=assess.phq9_score,
                gad7_score=assess.gad7_score,
                stress_level=assess.stress_level,
                risk_level=assess.risk_level.value
            )
            for assess in reversed(assessments)
        ]
        
        return trends
        
    except Exception as e:
        logger.error(f"❌ Failed to get trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve trends")
