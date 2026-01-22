"""
LSTM Model for Chat Summarization and Title Generation
"""
import torch
import torch.nn as nn
import json
import logging
from typing import List, Dict, Optional
from pathlib import Path

from src.utils.config import settings

logger = logging.getLogger(__name__)


class LSTMChatSummarizer(nn.Module):
    """LSTM model for generating chat titles and summaries"""
    
    def __init__(
        self,
        vocab_size: int,
        embedding_dim: int = 128,
        hidden_size: int = 256,
        num_layers: int = 2,
        dropout: float = 0.3
    ):
        super(LSTMChatSummarizer, self).__init__()
        
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # Embedding layer
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        
        # LSTM layers
        self.lstm = nn.LSTM(
            embedding_dim,
            hidden_size,
            num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=True
        )
        
        # Attention layer
        self.attention = nn.Linear(hidden_size * 2, 1)
        
        # Output layer for title generation
        self.fc_title = nn.Linear(hidden_size * 2, vocab_size)
        
        # Output layer for summary generation
        self.fc_summary = nn.Linear(hidden_size * 2, vocab_size)
    
    def attention_net(self, lstm_output):
        """Apply attention mechanism"""
        attn_weights = torch.softmax(self.attention(lstm_output), dim=1)
        context = torch.sum(attn_weights * lstm_output, dim=1)
        return context
    
    def forward(self, x, task='title'):
        """
        Forward pass
        Args:
            x: Input tensor [batch_size, seq_len]
            task: 'title' or 'summary'
        """
        # Embedding
        embedded = self.embedding(x)
        
        # LSTM
        lstm_out, (hidden, cell) = self.lstm(embedded)
        
        # Attention
        context = self.attention_net(lstm_out)
        
        # Task-specific output
        if task == 'title':
            output = self.fc_title(context)
        else:
            output = self.fc_summary(context)
        
        return output


class ChatTitleGenerator:
    """Service for generating chat titles using LSTM"""
    
    def __init__(self):
        self.model = None
        self.vocab = None
        self.idx2word = None
        self.word2idx = None
        self.max_length = settings.LSTM_MAX_LENGTH
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    def load_model(self):
        """Load pre-trained LSTM model and vocabulary"""
        try:
            # Load vocabulary
            vocab_path = Path(settings.LSTM_VOCAB_PATH)
            if vocab_path.exists():
                with open(vocab_path, 'r') as f:
                    vocab_data = json.load(f)
                    self.word2idx = vocab_data['word2idx']
                    self.idx2word = vocab_data['idx2word']
                    self.vocab = vocab_data['vocab']
                
                logger.info(f"✅ Loaded vocabulary with {len(self.vocab)} words")
            else:
                # Create default vocabulary
                self._create_default_vocab()
            
            # Load or create model
            model_path = Path(settings.LSTM_MODEL_PATH)
            vocab_size = len(self.vocab)
            
            self.model = LSTMChatSummarizer(
                vocab_size=vocab_size,
                hidden_size=settings.LSTM_HIDDEN_SIZE,
                num_layers=settings.LSTM_NUM_LAYERS
            ).to(self.device)
            
            if model_path.exists():
                self.model.load_state_dict(torch.load(model_path, map_location=self.device))
                logger.info(f"✅ Loaded LSTM model from {model_path}")
            else:
                logger.warning(f"⚠️ No pre-trained model found. Using untrained model.")
            
            self.model.eval()
            
        except Exception as e:
            logger.error(f"❌ Failed to load LSTM model: {e}")
            # Create minimal model for basic functionality
            self._create_default_vocab()
            self.model = None
    
    def _create_default_vocab(self):
        """Create a default vocabulary for basic operation"""
        common_words = [
            '<PAD>', '<UNK>', '<START>', '<END>',
            'anxiety', 'depression', 'stress', 'help', 'support', 'feeling',
            'mental', 'health', 'talk', 'chat', 'conversation', 'session',
            'about', 'today', 'my', 'i', 'am', 'feel', 'need', 'want'
        ]
        
        self.vocab = common_words
        self.word2idx = {word: idx for idx, word in enumerate(common_words)}
        self.idx2word = {idx: word for word, idx in self.word2idx.items()}
        
        # Save vocabulary
        vocab_path = Path(settings.LSTM_VOCAB_PATH)
        vocab_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(vocab_path, 'w') as f:
            json.dump({
                'vocab': self.vocab,
                'word2idx': self.word2idx,
                'idx2word': self.idx2word
            }, f)
    
    def tokenize(self, text: str) -> List[int]:
        """Convert text to token indices"""
        words = text.lower().split()
        tokens = [self.word2idx.get(word, self.word2idx['<UNK>']) for word in words]
        
        # Pad or truncate
        if len(tokens) < self.max_length:
            tokens += [self.word2idx['<PAD>']] * (self.max_length - len(tokens))
        else:
            tokens = tokens[:self.max_length]
        
        return tokens
    
    def generate_title(self, messages: List[str]) -> str:
        """Generate title from chat messages"""
        try:
            if not self.model:
                # Fallback: use simple rule-based title
                return self._generate_simple_title(messages)
            
            # Combine messages
            combined_text = " ".join(messages[:5])  # Use first 5 messages
            
            # Tokenize
            tokens = self.tokenize(combined_text)
            input_tensor = torch.tensor([tokens]).to(self.device)
            
            # Generate
            with torch.no_grad():
                output = self.model(input_tensor, task='title')
                predicted_indices = torch.argmax(output, dim=-1).cpu().numpy()[0]
            
            # Convert to words
            title_words = []
            for idx in predicted_indices[:10]:  # Max 10 words for title
                if idx in self.idx2word:
                    word = self.idx2word[str(idx)]
                    if word not in ['<PAD>', '<START>', '<END>', '<UNK>']:
                        title_words.append(word)
            
            if title_words:
                return " ".join(title_words).capitalize()
            else:
                return self._generate_simple_title(messages)
                
        except Exception as e:
            logger.error(f"❌ Title generation failed: {e}")
            return self._generate_simple_title(messages)
    
    def _generate_simple_title(self, messages: List[str]) -> str:
        """Fallback: Generate simple rule-based title"""
        if not messages:
            return "New Chat"
        
        first_message = messages[0][:60].strip()
        
        # Keyword-based titles
        keywords_map = {
            'anxiety': 'Anxiety Support',
            'anxious': 'Anxiety Support',
            'worried': 'Anxiety Support',
            'depression': 'Depression Help',
            'depressed': 'Depression Help',
            'sad': 'Feeling Down',
            'stress': 'Stress Management',
            'stressed': 'Stress Management',
            'help': 'Seeking Help',
            'suicide': 'Crisis Support',
            'kill': 'Crisis Support',
            'lonely': 'Loneliness',
            'alone': 'Feeling Alone',
            'sleep': 'Sleep Issues',
            'insomnia': 'Sleep Issues',
            'panic': 'Panic Support',
            'fear': 'Fears & Worries',
            'angry': 'Anger Management',
            'family': 'Family Issues',
            'relationship': 'Relationships',
            'work': 'Work Stress'
        }
        
        message_lower = first_message.lower()
        for keyword, title in keywords_map.items():
            if keyword in message_lower:
                return title
        
        # Use first few words if no keyword match
        words = first_message.split()[:4]
        if len(words) > 0:
            title = ' '.join(words)
            if len(title) > 30:
                title = title[:27] + '...'
            return title.capitalize()
        
        return "New Conversation"
    
    def generate_summary(self, messages: List[str]) -> str:
        """Generate summary from chat messages"""
        try:
            if len(messages) < 3:
                return "Brief conversation"
            
            # Simple extractive summary: take first user message and last AI response
            summary_parts = []
            
            if len(messages) > 0:
                summary_parts.append(f"Started with: {messages[0][:100]}")
            
            if len(messages) > 2:
                summary_parts.append(f"Discussed: {messages[len(messages)//2][:100]}")
            
            return ". ".join(summary_parts) + "."
            
        except Exception as e:
            logger.error(f"❌ Summary generation failed: {e}")
            return f"Chat with {len(messages)} messages"


# Global instance
chat_title_generator = ChatTitleGenerator()
