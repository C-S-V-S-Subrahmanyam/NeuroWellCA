"""
Assessment Service
Loads PHQ-9 and GAD-7 questionnaires from data/assessment_config.json
Provides methods to calculate scores and interpret risk levels
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class AssessmentService:
    """Service for managing mental health assessments"""
    
    def __init__(self):
        """Load assessment configuration from JSON file"""
        # Get the path to the data directory
        base_path = Path(__file__).parent.parent.parent.parent
        data_path = base_path / 'data' / 'assessment_config.json'
        
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                self.assessment_config = json.load(f)
            
            # Extract questionnaires
            self.phq9 = self.assessment_config['assessment_questionnaires']['phq9']
            self.gad7 = self.assessment_config['assessment_questionnaires']['gad7']
            
            print(f"✅ Assessment Service loaded successfully")
            print(f"   - PHQ-9 questions: {len(self.phq9['questions'])}")
            print(f"   - GAD-7 questions: {len(self.gad7['questions'])}")
            
        except FileNotFoundError:
            print(f"❌ Assessment config file not found at {data_path}")
            raise
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing assessment JSON: {e}")
            raise
    
    def get_phq9_questions(self) -> List[Dict]:
        """Get PHQ-9 questions"""
        return self.phq9['questions']
    
    def get_gad7_questions(self) -> List[Dict]:
        """Get GAD-7 questions"""
        return self.gad7['questions']
    
    def get_response_options(self, questionnaire: str = 'phq9') -> List[Dict]:
        """
        Get response options for a questionnaire
        
        Args:
            questionnaire: 'phq9' or 'gad7'
            
        Returns:
            List of response option dictionaries
        """
        if questionnaire == 'phq9':
            return self.phq9['response_options']
        elif questionnaire == 'gad7':
            return self.gad7['response_options']
        return []
    
    def calculate_phq9_score(self, responses: List[int]) -> Tuple[int, Dict]:
        """
        Calculate PHQ-9 score and interpret risk level
        
        Args:
            responses: List of 9 responses (0-3 each)
            
        Returns:
            Tuple of (total_score, interpretation_dict)
        """
        if len(responses) != 9:
            raise ValueError("PHQ-9 requires exactly 9 responses")
        
        # Validate response values
        for i, response in enumerate(responses):
            if not 0 <= response <= 3:
                raise ValueError(f"Response {i+1} must be between 0 and 3")
        
        # Calculate total score
        total_score = sum(responses)
        
        # Get interpretation
        interpretation = self._get_interpretation(total_score, 'phq9')
        
        # Check for crisis trigger (question 9 about self-harm)
        crisis_trigger = False
        if len(responses) >= 9 and responses[8] >= 2:  # Question 9, score >= 2
            crisis_trigger = True
        
        return total_score, {
            **interpretation,
            'crisis_trigger': crisis_trigger,
            'questionnaire': 'phq9'
        }
    
    def calculate_gad7_score(self, responses: List[int]) -> Tuple[int, Dict]:
        """
        Calculate GAD-7 score and interpret risk level
        
        Args:
            responses: List of 7 responses (0-3 each)
            
        Returns:
            Tuple of (total_score, interpretation_dict)
        """
        if len(responses) != 7:
            raise ValueError("GAD-7 requires exactly 7 responses")
        
        # Validate response values
        for i, response in enumerate(responses):
            if not 0 <= response <= 3:
                raise ValueError(f"Response {i+1} must be between 0 and 3")
        
        # Calculate total score
        total_score = sum(responses)
        
        # Get interpretation
        interpretation = self._get_interpretation(total_score, 'gad7')
        
        return total_score, {
            **interpretation,
            'crisis_trigger': False,
            'questionnaire': 'gad7'
        }
    
    def _get_interpretation(self, score: int, questionnaire: str) -> Dict:
        """
        Get interpretation for a score
        
        Args:
            score: Total score
            questionnaire: 'phq9' or 'gad7'
            
        Returns:
            Interpretation dictionary with level, description, recommendation, color
        """
        if questionnaire == 'phq9':
            scoring = self.phq9['scoring']
        elif questionnaire == 'gad7':
            scoring = self.gad7['scoring']
        else:
            return {}
        
        # Find matching interpretation range
        for interpretation in scoring['interpretation']:
            min_score = interpretation['range'][0]
            max_score = interpretation['range'][1]
            
            if min_score <= score <= max_score:
                return {
                    'level': interpretation['level'],
                    'description': interpretation.get('description', ''),
                    'recommendation': interpretation.get('recommendation', ''),
                    'color': interpretation['color'],
                    'score': score,
                    'max_score': scoring['max']
                }
        
        # Default if no match found
        return {
            'level': 'Unknown',
            'description': 'Score out of range',
            'recommendation': 'Please consult with a mental health professional',
            'color': 'gray',
            'score': score,
            'max_score': scoring['max']
        }
    
    def get_risk_level(self, phq9_score: Optional[int] = None, 
                      gad7_score: Optional[int] = None,
                      stress_score: Optional[int] = None) -> str:
        """
        Determine overall risk level based on multiple scores
        
        Args:
            phq9_score: PHQ-9 score (0-27)
            gad7_score: GAD-7 score (0-21)
            stress_score: Custom stress score (0-60)
            
        Returns:
            Overall risk level: 'None', 'Low', 'Moderate', 'High', 'Severe'
        """
        risk_levels = []
        
        # Evaluate PHQ-9
        if phq9_score is not None:
            if phq9_score >= 20:
                risk_levels.append(4)  # Severe
            elif phq9_score >= 15:
                risk_levels.append(3)  # Moderately severe
            elif phq9_score >= 10:
                risk_levels.append(2)  # Moderate
            elif phq9_score >= 5:
                risk_levels.append(1)  # Mild
            else:
                risk_levels.append(0)  # None
        
        # Evaluate GAD-7
        if gad7_score is not None:
            if gad7_score >= 15:
                risk_levels.append(3)  # Severe
            elif gad7_score >= 10:
                risk_levels.append(2)  # Moderate
            elif gad7_score >= 5:
                risk_levels.append(1)  # Mild
            else:
                risk_levels.append(0)  # Minimal
        
        # Evaluate stress score (custom scale)
        if stress_score is not None:
            if stress_score >= 45:
                risk_levels.append(3)  # High
            elif stress_score >= 30:
                risk_levels.append(2)  # Moderate
            elif stress_score >= 15:
                risk_levels.append(1)  # Low
            else:
                risk_levels.append(0)  # None
        
        # Determine overall risk level (use highest)
        if not risk_levels:
            return 'Unknown'
        
        max_risk = max(risk_levels)
        
        if max_risk >= 4:
            return 'Severe'
        elif max_risk >= 3:
            return 'High'
        elif max_risk >= 2:
            return 'Moderate'
        elif max_risk >= 1:
            return 'Low'
        else:
            return 'None'
    
    def get_example_profiles(self) -> List[Dict]:
        """Get example user profiles for testing"""
        return self.assessment_config.get('example_user_profiles', [])


# Create a singleton instance
_assessment_service = None


def get_assessment_service() -> AssessmentService:
    """Get or create the assessment service singleton"""
    global _assessment_service
    if _assessment_service is None:
        _assessment_service = AssessmentService()
    return _assessment_service
