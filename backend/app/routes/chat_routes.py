from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Conversation, CrisisLog, User
from app.services.crisis_service import get_crisis_service
from app.services.ai_service import get_ai_service
import logging
import requests
import uuid
from datetime import datetime

bp = Blueprint('chat', __name__)
logger = logging.getLogger(__name__)

# Ollama API endpoint
OLLAMA_API = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:latest"


@bp.route('/message', methods=['POST'])
@jwt_required()
def send_message():
    """
    Send message to AI chatbot
    
    Request body:
    {
        "message": "string",
        "session_id": "uuid" (optional)
    }
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('message'):
            return jsonify({'error': 'Message is required'}), 400
        
        user_message = data.get('message')
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        # 1. Check for crisis
        crisis_service = get_crisis_service()
        crisis_result = crisis_service.detect_crisis(user_message)
        
        # 2. Save user message
        user_conversation = Conversation(
            user_id=current_user_id,
            message_text=user_message,
            sender='user',
            session_id=session_id,
            created_at=datetime.utcnow()
        )
        db.session.add(user_conversation)
        db.session.flush()
        
        # 3. Handle crisis if detected
        if crisis_result.get('crisis_detected'):
            severity = crisis_result.get('severity')
            
            # Log crisis
            crisis_log = CrisisLog(
                user_id=current_user_id,
                conversation_id=user_conversation.conversation_id,
                crisis_score=crisis_service.calculate_crisis_score(user_message),
                keywords_matched=crisis_result.get('matched_keywords', []),
                action_taken=f"Crisis detected - {severity} severity",
                created_at=datetime.utcnow()
            )
            db.session.add(crisis_log)
            
            # Get user for guardian alert
            user = User.query.get(current_user_id)
            
            # Prepare crisis response
            if severity == 'high':
                ai_response = "I'm really concerned about what you're sharing. Your safety is the most important thing right now. Please reach out to one of these crisis helplines immediately:\n\n"
                
                # Add emergency contacts
                for contact in crisis_result.get('emergency_contacts', {}).get('india', []):
                    ai_response += f"• {contact['name']}: {contact['phone']}\n"
                
                ai_response += "\n🆘 If you're in immediate danger, please call emergency services or go to the nearest hospital.\n\n"
                
                if user and user.guardian_phone and user.guardian_consent:
                    ai_response += "I'm also alerting your guardian as you've given consent.\n\n"
                    # TODO: Send WhatsApp alert to guardian
                
                ai_response += "You matter, and help is available. Please reach out right now. 💙"
            else:
                ai_response = crisis_result.get('response_template', {}).get('message', '')
                ai_response += "\n\nWould you like to talk more about what you're going through?"
        else:
            # 4. Get AI persona and generate response
            ai_service = get_ai_service()
            system_prompt = ai_service.get_system_prompt()
            
            # Get conversation context
            context = ai_service.get_conversation_context(user_message)
            suggested_template = context.get('suggested_templates', [None])[0]
            
            # Generate AI response using Ollama
            try:
                ollama_response = requests.post(
                    OLLAMA_API,
                    json={
                        "model": OLLAMA_MODEL,
                        "prompt": f"{system_prompt}\n\nUser: {user_message}\n\nAssistant:",
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "top_p": 0.9
                        }
                    },
                    timeout=30
                )
                
                if ollama_response.status_code == 200:
                    ai_response = ollama_response.json().get('response', '')
                else:
                    # Fallback to template
                    if suggested_template:
                        ai_response = ai_service.format_response_with_template(suggested_template)
                    else:
                        ai_response = "I'm here to listen. Can you tell me more about what's on your mind?"
            except requests.exceptions.RequestException as e:
                logger.error(f"Ollama API error: {str(e)}")
                # Fallback response
                if suggested_template:
                    ai_response = ai_service.format_response_with_template(suggested_template)
                else:
                    ai_response = "I'm here to support you. How are you feeling today?"
        
        # 5. Save AI response
        ai_conversation = Conversation(
            user_id=current_user_id,
            message_text=ai_response,
            sender='ai',
            session_id=session_id,
            created_at=datetime.utcnow()
        )
        db.session.add(ai_conversation)
        db.session.commit()
        
        return jsonify({
            'response': ai_response,
            'session_id': session_id,
            'crisis_detected': crisis_result.get('crisis_detected', False),
            'severity': crisis_result.get('severity'),
            'emergency_contacts': crisis_result.get('emergency_contacts') if crisis_result.get('severity') == 'high' else None
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Chat error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/history', methods=['GET'])
@jwt_required()
def get_chat_history():
    """Get user's chat history"""
    try:
        current_user_id = get_jwt_identity()
        session_id = request.args.get('session_id')
        limit = int(request.args.get('limit', 50))
        
        query = Conversation.query.filter_by(user_id=current_user_id)
        
        if session_id:
            query = query.filter_by(session_id=session_id)
        
        conversations = query.order_by(Conversation.created_at.desc()).limit(limit).all()
        
        return jsonify({
            'conversations': [
                {
                    'conversation_id': c.conversation_id,
                    'message': c.message_text,
                    'sender': c.sender,
                    'session_id': c.session_id,
                    'timestamp': c.created_at.isoformat()
                }
                for c in reversed(conversations)  # Reverse to get chronological order
            ]
        }), 200
        
    except Exception as e:
        logger.error(f"Get chat history error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/sessions', methods=['GET'])
@jwt_required()
def get_chat_sessions():
    """Get list of user's chat sessions"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get unique session IDs with latest message
        sessions = db.session.query(
            Conversation.session_id,
            db.func.max(Conversation.created_at).label('last_message_at'),
            db.func.count(Conversation.conversation_id).label('message_count')
        ).filter_by(user_id=current_user_id).group_by(Conversation.session_id).order_by(db.desc('last_message_at')).all()
        
        return jsonify({
            'sessions': [
                {
                    'session_id': s.session_id,
                    'last_message_at': s.last_message_at.isoformat(),
                    'message_count': s.message_count
                }
                for s in sessions
            ]
        }), 200
        
    except Exception as e:
        logger.error(f"Get chat sessions error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
