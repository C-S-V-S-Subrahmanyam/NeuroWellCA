from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Assessment, CrisisLog
from app.services.assessment_service import get_assessment_service
from app.services.crisis_service import get_crisis_service
import logging
from datetime import datetime

bp = Blueprint('assessments', __name__)
logger = logging.getLogger(__name__)


@bp.route('/submit', methods=['POST'])
@jwt_required()
def submit_assessment():
    """
    Submit PHQ-9, GAD-7, and stress assessment
    
    Request body:
    {
        "phq9_responses": [0-3, 0-3, ...] (9 values),
        "gad7_responses": [0-3, 0-3, ...] (7 values),
        "stress_level": 0-10
    }
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        phq9_responses = data.get('phq9_responses', [])
        gad7_responses = data.get('gad7_responses', [])
        stress_level = data.get('stress_level', 5)
        
        # Validate responses
        if len(phq9_responses) != 9:
            return jsonify({'error': 'PHQ-9 requires 9 responses'}), 400
        if len(gad7_responses) != 7:
            return jsonify({'error': 'GAD-7 requires 7 responses'}), 400
        
        # Calculate scores using assessment service
        assessment_service = get_assessment_service()
        
        phq9_result = assessment_service.calculate_phq9_score(phq9_responses)
        gad7_result = assessment_service.calculate_gad7_score(gad7_responses)
        risk_assessment = assessment_service.get_risk_level(
            phq9_result['score'],
            gad7_result['score'],
            stress_level
        )
        
        # Create assessment record
        new_assessment = Assessment(
            user_id=current_user_id,
            phq9_score=phq9_result['score'],
            gad7_score=gad7_result['score'],
            stress_level=stress_level,
            risk_level=risk_assessment['risk_level'],
            created_at=datetime.utcnow()
        )
        
        db.session.add(new_assessment)
        
        # Mark user as having completed initial assessment
        from app.models import User
        user = User.query.get(current_user_id)
        if user and not user.has_completed_initial_assessment:
            user.has_completed_initial_assessment = True
        
        db.session.commit()
        
        # Check for crisis trigger (PHQ-9 Question 9: suicidal ideation)
        crisis_warning = None
        if phq9_result.get('crisis_trigger'):
            # Get crisis resources
            crisis_service = get_crisis_service()
            emergency_contacts = crisis_service.get_emergency_contacts('india')
            
            crisis_warning = {
                'message': 'Your responses indicate you may be experiencing thoughts of self-harm. Please reach out to a crisis helpline immediately:',
                'emergency_contacts': emergency_contacts,
                'severity': 'high'
            }
            
            # Log crisis
            crisis_log = CrisisLog(
                user_id=current_user_id,
                assessment_id=new_assessment.assessment_id,
                crisis_score=90,  # High score for suicidal ideation
                keywords_matched=['suicidal_ideation'],
                action_taken='Crisis warning displayed from PHQ-9 Q9',
                created_at=datetime.utcnow()
            )
            db.session.add(crisis_log)
            db.session.commit()
        
        return jsonify({
            'assessment_id': new_assessment.assessment_id,
            'phq9': {
                'score': phq9_result['score'],
                'max_score': phq9_result['max_score'],
                'interpretation': phq9_result['interpretation'],
                'severity': phq9_result['severity'],
                'color': phq9_result['color']
            },
            'gad7': {
                'score': gad7_result['score'],
                'max_score': gad7_result['max_score'],
                'interpretation': gad7_result['interpretation'],
                'severity': gad7_result['severity'],
                'color': gad7_result['color']
            },
            'overall_risk': {
                'risk_level': risk_assessment['risk_level'],
                'color': risk_assessment['color'],
                'message': risk_assessment['message'],
                'recommendations': risk_assessment['recommendations']
            },
            'crisis_warning': crisis_warning,
            'timestamp': new_assessment.created_at.isoformat()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Assessment submission error: {str(e)}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500


@bp.route('/history', methods=['GET'])
@jwt_required()
def get_assessment_history():
    """Get user's assessment history"""
    try:
        current_user_id = get_jwt_identity()
        
        assessments = Assessment.query.filter_by(user_id=current_user_id)\
            .order_by(Assessment.created_at.desc()).all()
        
        return jsonify({
            'assessments': [a.to_dict() for a in assessments]
        }), 200
        
    except Exception as e:
        logger.error(f"Get assessment history error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
