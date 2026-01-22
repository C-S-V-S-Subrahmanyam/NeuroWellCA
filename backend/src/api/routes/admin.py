"""
Admin routes for database management and viewing
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from src.models.database import get_db
from src.models.models import User, Assessment, Conversation, CrisisLog, ChatSession
from src.api.routes.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


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
