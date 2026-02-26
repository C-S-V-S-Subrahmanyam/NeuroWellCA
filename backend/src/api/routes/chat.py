"""
Chat routes with Ollama AI and Qdrant vector storage
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional, AsyncIterator
from datetime import datetime
import httpx
import uuid
import logging
import json
import asyncio

from src.models.database import get_db
from src.models.models import User, Conversation, ChatSession
from src.api.routes.auth import get_current_user
from src.api.dependencies import require_permission, require_any_permission
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


async def call_ollama_api_stream(prompt: str, context: List[str] = None) -> AsyncIterator[str]:
    """Call Ollama API for streaming AI response"""
    try:
        # Build context if available
        full_prompt = prompt
        if context:
            context_str = "\n".join(context[-10:])
            full_prompt = f"Previous conversation:\n{context_str}\n\nUser: {prompt}\n\nAssistant:"
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{settings.OLLAMA_API_URL}/api/generate",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "prompt": full_prompt,
                    "stream": True,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                    }
                },
                timeout=120.0
            ) as response:
                if response.status_code != 200:
                    logger.error(f"Ollama streaming error: {response.status_code}")
                    yield "I'm experiencing technical difficulties. Please try again."
                    return
                
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
                            if data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
                            
    except Exception as e:
        logger.error(f"❌ Ollama streaming failed: {e}")
        yield "I'm here to support you, but I'm having trouble responding right now. Please try again."


@router.post("/message/stream", dependencies=[Depends(require_permission("chat.create"))])
async def send_message_stream(
    message_data: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send message and get streaming AI response (SSE)"""
    
    async def generate_stream():
        try:
            # Generate or use existing session ID
            session_id = message_data.session_id or str(uuid.uuid4())
            
            # Send session_id first
            yield f"event: session\ndata: {json.dumps({'session_id': session_id})}\n\n"
            
            # Check for crisis
            crisis_result = crisis_service.detect_crisis(message_data.message)
            crisis_detected = crisis_result.get("is_crisis", False)
            
            if crisis_detected:
                yield f"event: crisis\ndata: {json.dumps({'detected': True})}\n\n"
            
            # Get conversation context
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
            
            # Prepare crisis response if needed
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
                yield f"event: chunk\ndata: {json.dumps({'chunk': crisis_message})}\n\n"
                ai_response = crisis_message
            else:
                # Stream AI response from Ollama
                ai_response = ""
                async for chunk in call_ollama_api_stream(message_data.message, context):
                    ai_response += chunk
                    yield f"event: chunk\ndata: {json.dumps({'chunk': chunk})}\n\n"
                    await asyncio.sleep(0.01)  # Small delay for smooth streaming
            
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
                # Generate title for new session
                title = chat_title_generator.generate_title([message_data.message])
                chat_session = ChatSession(
                    user_id=current_user.id,
                    session_id=session_id,
                    title=title,
                    message_count=2,
                    last_message_at=datetime.utcnow()
                )
                db.add(chat_session)
            else:
                chat_session.message_count += 2
                chat_session.last_message_at = datetime.utcnow()
            
            await db.commit()
            
            # Send completion event
            yield f"event: done\ndata: {json.dumps({'message': 'Stream complete'})}\n\n"
            
            logger.info(f"✅ Streaming message processed for user {current_user.username}, session {session_id}")
            
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Streaming failed: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/message", response_model=ChatResponse, dependencies=[Depends(require_permission("chat.create"))])
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


@router.get("/history/{session_id}", dependencies=[Depends(require_permission("chat.view"))])
async def get_chat_history(
    session_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get paginated chat history for a session"""
    try:
        # Get total count
        count_result = await db.execute(
            select(Conversation)
            .where(Conversation.session_id == session_id)
            .where(Conversation.user_id == current_user.id)
        )
        total = len(count_result.scalars().all())
        
        # Get paginated messages
        result = await db.execute(
            select(Conversation)
            .where(Conversation.session_id == session_id)
            .where(Conversation.user_id == current_user.id)
            .order_by(Conversation.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        conversations = result.scalars().all()
        
        messages = [
            {
                "id": conv.id,
                "message_text": conv.message_text,
                "sender": conv.sender,
                "created_at": conv.created_at.isoformat(),
                "crisis_detected": conv.crisis_detected or False
            }
            for conv in conversations
        ]
        
        return {
            "messages": messages,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + len(messages)) < total
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get chat history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat history"
        )


@router.get("/sessions", response_model=List[ChatSessionInfo], dependencies=[Depends(require_permission("chat.view"))])
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


@router.delete("/session/{session_id}", dependencies=[Depends(require_permission("chat.delete"))])
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


class RenameSessionRequest(BaseModel):
    title: str


@router.patch("/session/{session_id}/rename", dependencies=[Depends(require_permission("chat.view"))])
async def rename_chat_session(
    session_id: str,
    request: RenameSessionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Rename a chat session"""
    try:
        # Find session
        result = await db.execute(
            select(ChatSession)
            .where(ChatSession.session_id == session_id)
            .where(ChatSession.user_id == current_user.id)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Update title
        session.title = request.title[:200]  # Limit to 200 chars
        await db.commit()
        
        logger.info(f"✅ Renamed session {session_id} to '{request.title}'")
        
        return {"message": "Session renamed successfully", "title": session.title}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Failed to rename session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to rename session"
        )

