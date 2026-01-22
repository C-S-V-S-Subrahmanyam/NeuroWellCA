"""
Chat routes with Ollama AI and Qdrant vector storage
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import httpx
import uuid
import logging

from src.models.database import get_db
from src.models.models import User, Conversation, ChatSession
from src.api.routes.auth import get_current_user
from src.services.qdrant_service import qdrant_service
from src.services.crisis_service import crisis_service
from src.ml_models.lstm_summarizer import chat_title_generator
from src.utils.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    crisis_detected: bool = False
    crisis_resources: Optional[List[dict]] = None


class SessionMessage(BaseModel):
    id: int
    message_text: str
    sender: str
    created_at: datetime
    crisis_detected: bool


class ChatSessionInfo(BaseModel):
    session_id: str
    title: str
    message_count: int
    started_at: datetime
    last_message_at: Optional[datetime]


# Helper function to call Ollama
async def call_ollama_api(prompt: str, context: List[str] = None) -> str:
    """Call Ollama API for AI response"""
    try:
        # Build context if available
        full_prompt = prompt
        if context:
            context_str = "\n".join(context[-10:])  # Last 10 messages
            full_prompt = f"Previous conversation:\n{context_str}\n\nUser: {prompt}\n\nAssistant:"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.OLLAMA_API_URL}/api/generate",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "I'm here to listen and support you.")
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return "I'm experiencing technical difficulties. Please try again."
                
    except Exception as e:
        logger.error(f"❌ Ollama API call failed: {e}")
        return "I'm here to support you, but I'm having trouble responding right now. Please try again."


@router.post("/message", response_model=ChatResponse)
async def send_message(
    message_data: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send message and get AI response"""
    try:
        # Generate or use existing session ID
        session_id = message_data.session_id or str(uuid.uuid4())
        
        # Check for crisis
        crisis_result = crisis_service.detect_crisis(message_data.message)
        crisis_detected = crisis_result.get("is_crisis", False)
        
        # Get conversation context from Qdrant
        context_messages = await qdrant_service.get_session_context(session_id, limit=10)
        context = [f"{msg['sender']}: {msg['message_text']}" for msg in context_messages]
        
        # Save user message
        user_conversation = Conversation(
            user_id=current_user.id,
            session_id=session_id,
            message_text=message_data.message,
            sender="user",
            crisis_detected=crisis_detected,
            sentiment_score=crisis_result.get("score", 0.0)
        )
        db.add(user_conversation)
        await db.flush()
        
        # Add to Qdrant
        vector_id = await qdrant_service.add_conversation(
            conversation_id=user_conversation.id,
            user_id=current_user.id,
            session_id=session_id,
            message_text=message_data.message,
            sender="user",
            metadata={"crisis_detected": crisis_detected}
        )
        user_conversation.vector_id = vector_id
        
        # Get AI response from Ollama
        ai_response = await call_ollama_api(message_data.message, context)
        
        # If crisis detected, override with crisis response
        crisis_message = None
        if crisis_detected:
            crisis_message = (
                "🚨 I'm really concerned about what you're sharing. Your safety is the most important thing, "
                "and I want you to know you don't have to face this alone.\n\n"
                "Please reach out to a crisis helpline RIGHT NOW:\n"
                "📞 KIRAN Mental Health: 1800-599-0019 (24/7, Free)\n"
                "📞 Sneha India: 044-24640050 (24/7)\n"
                "📞 Vandrevala Foundation: 1860-266-2345 (24/7)\n"
                "📞 Emergency: 112\n\n"
                "These counselors are trained for moments like this. Please call them now. "
                "You matter, and help is available."
            )
            # Log crisis event
            logger.warning(f"⚠️ CRISIS DETECTED for user {current_user.id}: {message_data.message[:50]}...")
            
            # Override AI response with crisis message
            ai_response = crisis_message
        
        # Save AI response
        ai_conversation = Conversation(
            user_id=current_user.id,
            session_id=session_id,
            message_text=ai_response,
            sender="ai",
            crisis_detected=False
        )
        db.add(ai_conversation)
        await db.flush()
        
        # Add AI response to Qdrant
        ai_vector_id = await qdrant_service.add_conversation(
            conversation_id=ai_conversation.id,
            user_id=current_user.id,
            session_id=session_id,
            message_text=ai_response,
            sender="ai"
        )
        ai_conversation.vector_id = ai_vector_id
        
        # Update or create chat session
        result = await db.execute(
            select(ChatSession).where(ChatSession.session_id == session_id)
        )
        chat_session = result.scalar_one_or_none()
        
        if not chat_session:
            # Create new session
            chat_session = ChatSession(
                user_id=current_user.id,
                session_id=session_id,
                message_count=2,
                last_message_at=datetime.utcnow()
            )
            db.add(chat_session)
        else:
            # Update existing session
            chat_session.message_count += 2
            chat_session.last_message_at = datetime.utcnow()
        
        await db.commit()
        
        # Prepare response
        response_data = ChatResponse(
            response=ai_response,
            session_id=session_id,
            crisis_detected=crisis_detected
        )
        
        if crisis_detected:
            response_data.crisis_message = crisis_message
            response_data.crisis_resources = crisis_result.get("resources", [])
        
        logger.info(f"✅ Message processed for user {current_user.username}, session {session_id}")
        
        return response_data
        
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Message processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message"
        )


@router.get("/history/{session_id}", response_model=List[SessionMessage])
async def get_chat_history(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get chat history for a session"""
    try:
        result = await db.execute(
            select(Conversation)
            .where(Conversation.session_id == session_id)
            .where(Conversation.user_id == current_user.id)
            .order_by(Conversation.created_at.asc())
        )
        conversations = result.scalars().all()
        
        return [
            SessionMessage(
                id=conv.id,
                message_text=conv.message_text,
                sender=conv.sender,
                created_at=conv.created_at,
                crisis_detected=conv.crisis_detected or False
            )
            for conv in conversations
        ]
        
    except Exception as e:
        logger.error(f"❌ Failed to get chat history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat history"
        )


@router.get("/sessions", response_model=List[ChatSessionInfo])
async def get_chat_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all chat sessions for current user"""
    try:
        result = await db.execute(
            select(ChatSession)
            .where(ChatSession.user_id == current_user.id)
            .order_by(ChatSession.last_message_at.desc())
        )
        sessions = result.scalars().all()
        
        # Generate titles for sessions without titles
        for session in sessions:
            if not session.title:
                # Get messages for this session
                conv_result = await db.execute(
                    select(Conversation)
                    .where(Conversation.session_id == session.session_id)
                    .where(Conversation.sender == "user")
                    .order_by(Conversation.created_at.asc())
                    .limit(5)
                )
                messages = [conv.message_text for conv in conv_result.scalars().all()]
                
                # Generate title using LSTM
                session.title = chat_title_generator.generate_title(messages)
                await db.commit()
        
        return [
            ChatSessionInfo(
                session_id=session.session_id,
                title=session.title or "New Chat",
                message_count=session.message_count,
                started_at=session.started_at,
                last_message_at=session.last_message_at
            )
            for session in sessions
        ]
        
    except Exception as e:
        logger.error(f"❌ Failed to get chat sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat sessions"
        )


@router.delete("/session/{session_id}")
async def delete_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a chat session"""
    try:
        # Delete conversations from database
        result = await db.execute(
            select(Conversation)
            .where(Conversation.session_id == session_id)
            .where(Conversation.user_id == current_user.id)
        )
        conversations = result.scalars().all()
        
        for conv in conversations:
            await db.delete(conv)
        
        # Delete session
        result = await db.execute(
            select(ChatSession)
            .where(ChatSession.session_id == session_id)
            .where(ChatSession.user_id == current_user.id)
        )
        session = result.scalar_one_or_none()
        
        if session:
            await db.delete(session)
        
        await db.commit()
        
        logger.info(f"✅ Deleted session {session_id}")
        
        return {"message": "Session deleted successfully"}
        
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Failed to delete session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete session"
        )
