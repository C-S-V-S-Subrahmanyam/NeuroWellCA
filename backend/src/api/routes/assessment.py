"""
Assessment routes for PHQ-9 and GAD-7
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
import logging

from src.models.database import get_db
from src.models.models import User, Assessment, RiskLevel
from src.api.routes.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models
class AssessmentSubmit(BaseModel):
    phq9_answers: List[int]  # 9 questions, 0-3 each
    gad7_answers: List[int]  # 7 questions, 0-3 each
    stress_level: int  # 0-10
    notes: Optional[str] = None


class AssessmentResponse(BaseModel):
    id: int
    phq9_score: int
    gad7_score: int
    stress_level: int
    risk_level: str
    created_at: datetime
    
    class Config:
        from_attributes = True


def calculate_risk_level(phq9_score: int, gad7_score: int, stress_level: int) -> RiskLevel:
    """Calculate overall risk level based on scores"""
    # PHQ-9: 0-4 minimal, 5-9 mild, 10-14 moderate, 15-19 moderately severe, 20+ severe
    # GAD-7: 0-4 minimal, 5-9 mild, 10-14 moderate, 15+ severe
    
    if phq9_score >= 20 or gad7_score >= 15 or stress_level >= 9:
        return RiskLevel.SEVERE
    elif phq9_score >= 15 or gad7_score >= 10 or stress_level >= 7:
        return RiskLevel.MODERATELY_SEVERE
    elif phq9_score >= 10 or gad7_score >= 5 or stress_level >= 5:
        return RiskLevel.MODERATE
    elif phq9_score >= 5 or stress_level >= 3:
        return RiskLevel.MILD
    else:
        return RiskLevel.LOW


@router.post("/submit", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
async def submit_assessment(
    assessment_data: AssessmentSubmit,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Submit new assessment"""
    try:
        # Validate answers
        if len(assessment_data.phq9_answers) != 9:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PHQ-9 requires 9 answers"
            )
        
        if len(assessment_data.gad7_answers) != 7:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GAD-7 requires 7 answers"
            )
        
        # Calculate scores
        phq9_score = sum(assessment_data.phq9_answers)
        gad7_score = sum(assessment_data.gad7_answers)
        
        # Calculate risk level
        risk_level = calculate_risk_level(
            phq9_score,
            gad7_score,
            assessment_data.stress_level
        )
        
        # Create assessment
        assessment = Assessment(
            user_id=current_user.id,
            phq9_score=phq9_score,
            gad7_score=gad7_score,
            stress_level=assessment_data.stress_level,
            risk_level=risk_level,
            phq9_q1=assessment_data.phq9_answers[0],
            phq9_q2=assessment_data.phq9_answers[1],
            phq9_q3=assessment_data.phq9_answers[2],
            phq9_q4=assessment_data.phq9_answers[3],
            phq9_q5=assessment_data.phq9_answers[4],
            phq9_q6=assessment_data.phq9_answers[5],
            phq9_q7=assessment_data.phq9_answers[6],
            phq9_q8=assessment_data.phq9_answers[7],
            phq9_q9=assessment_data.phq9_answers[8],
            gad7_q1=assessment_data.gad7_answers[0],
            gad7_q2=assessment_data.gad7_answers[1],
            gad7_q3=assessment_data.gad7_answers[2],
            gad7_q4=assessment_data.gad7_answers[3],
            gad7_q5=assessment_data.gad7_answers[4],
            gad7_q6=assessment_data.gad7_answers[5],
            gad7_q7=assessment_data.gad7_answers[6],
            notes=assessment_data.notes
        )
        
        db.add(assessment)
        
        # Mark user as having completed initial assessment
        if not current_user.has_completed_initial_assessment:
            current_user.has_completed_initial_assessment = True
        
        await db.commit()
        await db.refresh(assessment)
        
        logger.info(f"✅ Assessment submitted by user {current_user.username}")
        
        return assessment
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Assessment submission failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit assessment"
        )


@router.get("/history", response_model=List[AssessmentResponse])
async def get_assessment_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get assessment history for current user"""
    try:
        from sqlalchemy import select
        
        result = await db.execute(
            select(Assessment)
            .where(Assessment.user_id == current_user.id)
            .order_by(Assessment.created_at.desc())
        )
        assessments = result.scalars().all()
        
        return assessments
        
    except Exception as e:
        logger.error(f"❌ Failed to get assessment history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve assessment history"
        )
