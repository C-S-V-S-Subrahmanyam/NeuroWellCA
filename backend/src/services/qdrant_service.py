"""
Qdrant vector database service
"""
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
import uuid
import logging

from src.utils.config import settings

logger = logging.getLogger(__name__)


class QdrantService:
    """Service for managing Qdrant vector database operations"""
    
    def __init__(self):
        self.client = None
        self.encoder = None
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        self.embedding_dim = settings.QDRANT_EMBEDDING_DIM
    
    async def initialize_collections(self):
        """Initialize Qdrant client and create collections"""
        try:
            # Initialize Qdrant client
            self.client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None,
                timeout=30
            )
            
            # Initialize sentence transformer for embeddings
            self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if self.collection_name not in collection_names:
                # Create collection
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dim,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"✅ Created Qdrant collection: {self.collection_name}")
            else:
                logger.info(f"✅ Qdrant collection already exists: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Qdrant: {e}")
            raise
    
    def create_embedding(self, text: str) -> List[float]:
        """Create vector embedding from text"""
        if not self.encoder:
            raise RuntimeError("Encoder not initialized. Call initialize_collections first.")
        
        embedding = self.encoder.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    async def add_conversation(
        self,
        conversation_id: int,
        user_id: int,
        session_id: str,
        message_text: str,
        sender: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """Add conversation message to vector database"""
        try:
            # Create embedding
            vector = self.create_embedding(message_text)
            
            # Generate unique point ID
            point_id = str(uuid.uuid4())
            
            # Prepare payload
            payload = {
                "conversation_id": conversation_id,
                "user_id": user_id,
                "session_id": session_id,
                "message_text": message_text,
                "sender": sender,
                **(metadata or {})
            }
            
            # Insert into Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=point_id,
                        vector=vector,
                        payload=payload
                    )
                ]
            )
            
            logger.info(f"✅ Added conversation {conversation_id} to Qdrant with ID: {point_id}")
            return point_id
            
        except Exception as e:
            logger.error(f"❌ Failed to add conversation to Qdrant: {e}")
            raise
    
    async def search_similar_conversations(
        self,
        query_text: str,
        user_id: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict]:
        """Search for similar conversations"""
        try:
            # Create query embedding
            query_vector = self.create_embedding(query_text)
            
            # Prepare filter
            search_filter = None
            if user_id:
                search_filter = {
                    "must": [
                        {"key": "user_id", "match": {"value": user_id}}
                    ]
                }
            
            # Search
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=search_filter,
                limit=limit
            )
            
            # Format results
            formatted_results = [
                {
                    "score": hit.score,
                    "conversation_id": hit.payload.get("conversation_id"),
                    "message_text": hit.payload.get("message_text"),
                    "sender": hit.payload.get("sender"),
                    "session_id": hit.payload.get("session_id")
                }
                for hit in results
            ]
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"❌ Failed to search Qdrant: {e}")
            return []
    
    async def get_session_context(self, session_id: str, limit: int = 10) -> List[Dict]:
        """Get recent conversations from a session"""
        try:
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter={
                    "must": [
                        {"key": "session_id", "match": {"value": session_id}}
                    ]
                },
                limit=limit
            )
            
            conversations = [
                {
                    "message_text": point.payload.get("message_text"),
                    "sender": point.payload.get("sender")
                }
                for point in results[0]
            ]
            
            return conversations
            
        except Exception as e:
            logger.error(f"❌ Failed to get session context: {e}")
            return []
    
    async def delete_user_conversations(self, user_id: int):
        """Delete all conversations for a user"""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector={
                    "filter": {
                        "must": [
                            {"key": "user_id", "match": {"value": user_id}}
                        ]
                    }
                }
            )
            logger.info(f"✅ Deleted all conversations for user {user_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to delete user conversations: {e}")
            raise


# Global instance
qdrant_service = QdrantService()
