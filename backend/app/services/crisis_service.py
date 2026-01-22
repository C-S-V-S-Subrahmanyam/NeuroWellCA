"""
Crisis Detection Service
Loads crisis keywords and emergency contacts from data/crisis_detection.json
Provides methods to detect crisis situations in user messages
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional


class CrisisDetectionService:
    """Service for detecting crisis situations in user messages"""
    
    def __init__(self):
        """Load crisis detection data from JSON file"""
        # Get the path to the data directory
        base_path = Path(__file__).parent.parent.parent.parent
        data_path = base_path / 'data' / 'crisis_detection.json'
        
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                self.crisis_data = json.load(f)
            
            # Extract keywords by severity
            self.high_keywords = [kw.lower() for kw in self.crisis_data['crisis_keywords']['high_severity']]
            self.medium_keywords = [kw.lower() for kw in self.crisis_data['crisis_keywords']['medium_severity']]
            self.low_keywords = [kw.lower() for kw in self.crisis_data['crisis_keywords']['low_severity']]
            
            # Store emergency contacts
            self.emergency_contacts = self.crisis_data['emergency_contacts']
            
            # Store response templates
            self.response_templates = self.crisis_data['crisis_response_templates']
            
            print(f"✅ Crisis Detection Service loaded successfully")
            print(f"   - High severity keywords: {len(self.high_keywords)}")
            print(f"   - Medium severity keywords: {len(self.medium_keywords)}")
            print(f"   - Low severity keywords: {len(self.low_keywords)}")
            
        except FileNotFoundError:
            print(f"❌ Crisis detection data file not found at {data_path}")
            raise
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing crisis detection JSON: {e}")
            raise
    
    def detect_crisis(self, message: str) -> Dict:
        """
        Detect crisis situation in a message
        
        Args:
            message: User message text
            
        Returns:
            Dictionary with crisis detection results:
            {
                'crisis_detected': bool,
                'severity': str (high/medium/low) or None,
                'matched_keywords': list of matched keywords,
                'response_template': dict with actions/message,
                'emergency_contacts': dict (only for high severity)
            }
        """
        if not message:
            return {'crisis_detected': False}
        
        message_lower = message.lower()
        matched_keywords = []
        severity = None
        
        # Check high severity first
        for keyword in self.high_keywords:
            if keyword in message_lower:
                matched_keywords.append(keyword)
                severity = 'high'
        
        # If no high severity, check medium
        if not severity:
            for keyword in self.medium_keywords:
                if keyword in message_lower:
                    matched_keywords.append(keyword)
                    severity = 'medium'
        
        # If no medium severity, check low
        if not severity:
            for keyword in self.low_keywords:
                if keyword in message_lower:
                    matched_keywords.append(keyword)
                    severity = 'low'
        
        # If crisis detected, return detailed response
        if severity:
            result = {
                'crisis_detected': True,
                'severity': severity,
                'matched_keywords': matched_keywords,
                'response_template': self.response_templates[severity]
            }
            
            # Add emergency contacts for high severity
            if severity == 'high':
                result['emergency_contacts'] = self.emergency_contacts
            
            return result
        
        return {'crisis_detected': False}
    
    def get_emergency_contacts(self, region: str = 'india') -> List[Dict]:
        """
        Get emergency contacts for a specific region
        
        Args:
            region: 'india' or 'international'
            
        Returns:
            List of emergency contact dictionaries
        """
        return self.emergency_contacts.get(region, [])
    
    def get_all_emergency_contacts(self) -> Dict:
        """Get all emergency contacts"""
        return self.emergency_contacts
    
    def calculate_crisis_score(self, message: str) -> int:
        """
        Calculate a crisis score (0-100) based on keyword matches
        
        Args:
            message: User message text
            
        Returns:
            Crisis score: 0 (no crisis) to 100 (severe crisis)
        """
        if not message:
            return 0
        
        message_lower = message.lower()
        score = 0
        
        # Count high severity matches (30 points each)
        high_matches = sum(1 for kw in self.high_keywords if kw in message_lower)
        score += min(high_matches * 30, 90)  # Cap at 90
        
        # Count medium severity matches (15 points each)
        if score < 50:  # Only count if no high severity
            medium_matches = sum(1 for kw in self.medium_keywords if kw in message_lower)
            score += min(medium_matches * 15, 60)  # Cap at 60
        
        # Count low severity matches (10 points each)
        if score < 30:  # Only count if no medium/high severity
            low_matches = sum(1 for kw in self.low_keywords if kw in message_lower)
            score += min(low_matches * 10, 30)  # Cap at 30
        
        return min(score, 100)  # Ensure max is 100


# Create a singleton instance
_crisis_service = None


def get_crisis_service() -> CrisisDetectionService:
    """Get or create the crisis detection service singleton"""
    global _crisis_service
    if _crisis_service is None:
        _crisis_service = CrisisDetectionService()
    return _crisis_service
