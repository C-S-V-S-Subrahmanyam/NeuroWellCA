"""
AI Persona Service
Loads AI personality and conversation guidelines from data/ai_persona_config.json
Provides methods to generate empathetic responses
"""

import json
from pathlib import Path
from typing import Dict, List, Optional


class AIPersonaService:
    """Service for managing AI persona and generating responses"""
    
    def __init__(self):
        """Load AI persona configuration from JSON file"""
        # Get the path to the data directory
        base_path = Path(__file__).parent.parent.parent.parent
        data_path = base_path / 'data' / 'ai_persona_config.json'
        
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                self.persona_config = json.load(f)
            
            # Extract configuration sections
            self.persona = self.persona_config['ai_persona']
            self.conversation_guidelines = self.persona_config['conversation_guidelines']
            self.response_templates = self.persona_config['response_templates']
            self.crisis_prompts = self.persona_config['crisis_detection_prompts']
            
            print(f"✅ AI Persona Service loaded successfully")
            print(f"   - Persona: {self.persona['name']}")
            print(f"   - Role: {self.persona['role']}")
            print(f"   - Response templates: {len(self.response_templates)}")
            
        except FileNotFoundError:
            print(f"❌ AI persona config file not found at {data_path}")
            raise
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing AI persona JSON: {e}")
            raise
    
    def get_system_prompt(self) -> str:
        """
        Generate the system prompt for the AI model (Ollama)
        
        Returns:
            System prompt string with personality and guidelines
        """
        prompt_parts = [
            f"You are {self.persona['name']}, a {self.persona['role']}.",
            "",
            "PERSONALITY:",
        ]
        
        # Add personality traits
        for trait in self.persona['personality']:
            prompt_parts.append(f"- {trait}")
        
        prompt_parts.extend([
            "",
            "COMMUNICATION STYLE:",
            f"- Tone: {self.persona['communication_style']['tone']}",
            f"- Response length: {self.persona['communication_style']['response_length']}",
            f"- Emoji usage: {self.persona['communication_style']['emoji_usage']}",
            "",
            "YOU MUST AVOID:",
        ])
        
        # Add what to avoid
        for avoid in self.persona['communication_style']['avoid']:
            prompt_parts.append(f"- {avoid}")
        
        prompt_parts.extend([
            "",
            "CORE PRINCIPLES:",
        ])
        
        # Add core principles
        for principle in self.persona['core_principles']:
            prompt_parts.append(f"- {principle}")
        
        prompt_parts.extend([
            "",
            "CONVERSATION GUIDELINES:",
            "- Use active listening phrases to show empathy",
            "- Validate user feelings before offering solutions",
            "- Use smooth transitions when changing topics",
            "- End conversations with supportive closing messages",
            "",
            "Remember: You are here to listen, support, and guide - not to diagnose or prescribe."
        ])
        
        return "\n".join(prompt_parts)
    
    def get_opening_message(self, index: int = 0) -> str:
        """
        Get a conversation opening message
        
        Args:
            index: Index of the opening message (0-2)
            
        Returns:
            Opening message string
        """
        messages = self.conversation_guidelines['opening_messages']
        if 0 <= index < len(messages):
            return messages[index]
        return messages[0]
    
    def get_random_opening_message(self) -> str:
        """Get a random opening message"""
        import random
        return random.choice(self.conversation_guidelines['opening_messages'])
    
    def get_active_listening_phrase(self, index: int = 0) -> str:
        """Get an active listening phrase"""
        phrases = self.conversation_guidelines['active_listening_phrases']
        if 0 <= index < len(phrases):
            return phrases[index]
        return phrases[0]
    
    def get_validation_statement(self, index: int = 0) -> str:
        """Get a validation statement"""
        statements = self.conversation_guidelines['validation_statements']
        if 0 <= index < len(statements):
            return statements[index]
        return statements[0]
    
    def get_response_template(self, scenario: str) -> Optional[Dict]:
        """
        Get a response template for a specific scenario
        
        Args:
            scenario: One of 'anxiety', 'depression', 'academic_stress', 
                     'loneliness', 'exam_anxiety'
            
        Returns:
            Response template dictionary or None
        """
        return self.response_templates.get(scenario)
    
    def get_crisis_prompt(self, crisis_type: str) -> Optional[Dict]:
        """
        Get a crisis prompt for a specific type
        
        Args:
            crisis_type: One of 'suicidal_ideation', 'self_harm', 'severe_distress'
            
        Returns:
            Crisis prompt dictionary or None
        """
        return self.crisis_prompts.get(crisis_type)
    
    def format_response_with_template(self, scenario: str, user_context: Dict = None) -> str:
        """
        Format a response using a template
        
        Args:
            scenario: Scenario name
            user_context: Optional dictionary with user-specific context
            
        Returns:
            Formatted response string
        """
        template = self.get_response_template(scenario)
        if not template:
            return ""
        
        response_parts = []
        
        # Add empathy statement
        response_parts.append(template['empathy'])
        
        # Add suggestion
        response_parts.append(template['suggestion'])
        
        # Add follow-up
        response_parts.append(template['follow_up'])
        
        return "\n\n".join(response_parts)
    
    def get_conversation_context(self, user_message: str, detected_emotion: str = None) -> Dict:
        """
        Analyze user message and provide conversation context
        
        Args:
            user_message: The user's message
            detected_emotion: Optional emotion detected from message
            
        Returns:
            Dictionary with conversation context and suggestions
        """
        context = {
            'message': user_message,
            'detected_emotion': detected_emotion,
            'suggested_templates': []
        }
        
        # Detect potential scenarios from message keywords
        message_lower = user_message.lower()
        
        # Check for anxiety indicators
        if any(word in message_lower for word in ['anxious', 'worried', 'nervous', 'panic', 'stress']):
            context['suggested_templates'].append('anxiety')
        
        # Check for depression indicators
        if any(word in message_lower for word in ['sad', 'depressed', 'hopeless', 'worthless', 'empty']):
            context['suggested_templates'].append('depression')
        
        # Check for academic stress indicators
        if any(word in message_lower for word in ['exam', 'test', 'study', 'assignment', 'grade', 'academic']):
            context['suggested_templates'].append('exam_anxiety')
            context['suggested_templates'].append('academic_stress')
        
        # Check for loneliness indicators
        if any(word in message_lower for word in ['lonely', 'alone', 'isolated', 'nobody']):
            context['suggested_templates'].append('loneliness')
        
        return context


# Create a singleton instance
_ai_service = None


def get_ai_service() -> AIPersonaService:
    """Get or create the AI persona service singleton"""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIPersonaService()
    return _ai_service
