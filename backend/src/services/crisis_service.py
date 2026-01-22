"""
Crisis detection service
"""
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import json
from pathlib import Path
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class CrisisService:
    """Service for detecting crisis situations in messages"""
    
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        self.crisis_keywords = self._load_crisis_keywords()
        self.resources = self._load_resources()
    
    def _load_crisis_keywords(self) -> Dict:
        """Load crisis detection keywords"""
        try:
            crisis_config_path = Path("data/crisis_detection.json")
            if crisis_config_path.exists():
                with open(crisis_config_path, 'r') as f:
                    data = json.load(f)
                    return data.get("crisis_keywords", {})
            else:
                # Default keywords
                return {
                    "suicide": ["suicide", "kill myself", "end my life", "want to die"],
                    "self_harm": ["cut myself", "hurt myself", "self-harm"],
                    "severe_depression": ["can't go on", "no point", "worthless", "hopeless"]
                }
        except Exception as e:
            logger.error(f"Failed to load crisis keywords: {e}")
            return {}
    
    def _load_resources(self) -> List[Dict]:
        """Load mental health resources"""
        try:
            resources_path = Path("data/mental_health_resources.json")
            if resources_path.exists():
                with open(resources_path, 'r') as f:
                    data = json.load(f)
                    return data.get("crisis_resources", [])
            else:
                # Default resources
                return [
                    {
                        "name": "National Suicide Prevention Lifeline",
                        "contact": "988",
                        "type": "hotline"
                    },
                    {
                        "name": "Crisis Text Line",
                        "contact": "Text HOME to 741741",
                        "type": "text"
                    }
                ]
        except Exception as e:
            logger.error(f"Failed to load resources: {e}")
            return []
    
    def detect_crisis(self, message: str) -> Dict:
        """
        Detect crisis in message
        Returns: {
            "is_crisis": bool,
            "score": int (0-5),
            "keywords_detected": List[str],
            "resources": List[Dict]
        }
        """
        message_lower = message.lower().strip()
        
        # Remove extra spaces and normalize
        message_normalized = ' '.join(message_lower.split())
        
        # Check for crisis keywords
        crisis_score = 0
        detected_keywords = []
        high_severity_detected = False
        
        for category, keywords in self.crisis_keywords.items():
            for keyword in keywords:
                # Check both original and normalized message
                if keyword in message_lower or keyword in message_normalized:
                    if category == "high_severity":
                        crisis_score += 3  # High severity gets more weight
                        high_severity_detected = True
                    elif category == "medium_severity":
                        crisis_score += 2
                    else:
                        crisis_score += 1
                    
                    detected_keywords.append(keyword)
                    break  # Only count once per category
        
        # Sentiment analysis
        sentiment = self.analyzer.polarity_scores(message)
        
        # Very negative sentiment increases crisis score
        if sentiment['compound'] < -0.7:
            crisis_score += 1
        elif sentiment['compound'] < -0.5:
            crisis_score += 0.5
        
        # Determine if this is a crisis
        # High severity keyword = immediate crisis
        # Or score >= 3 from multiple medium/low keywords
        is_crisis = high_severity_detected or crisis_score >= 3
        
        result = {
            "is_crisis": is_crisis,
            "score": crisis_score,
            "keywords_detected": detected_keywords,
            "sentiment": sentiment
        }
        
        if is_crisis:
            result["resources"] = self.resources
        
        return result


# Global instance
crisis_service = CrisisService()
