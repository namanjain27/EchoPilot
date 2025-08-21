"""
Intent classification module for EchoPilot
Analyzes user messages to determine intent, urgency, and sentiment using ML models
"""

from enum import Enum
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
import numpy as np
from sentence_transformers import SentenceTransformer
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntentType(Enum):
    """Types of user intents"""
    QUERY = "query"
    COMPLAINT = "complaint"
    SERVICE_REQUEST = "service_request"


class Urgency(Enum):
    """Urgency levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Sentiment(Enum):
    """Sentiment types"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


@dataclass
class IntentAnalysis:
    """Result of intent analysis"""
    intent: IntentType
    urgency: Urgency
    sentiment: Sentiment
    confidence: float


class IntentClassifier:
    """Classifies user messages to determine intent, urgency, and sentiment using ML models"""
    
    def __init__(self):
        """Initialize the intent classifier with pre-trained models"""
        try:
            # Load sentence transformer model for embeddings
            self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Loaded sentence transformer model successfully")
            
            # Initialize training data for similarity-based classification
            self._init_training_data()
            
            # Pre-compute embeddings for training examples
            self._compute_training_embeddings()
            
        except Exception as e:
            logger.error(f"Failed to initialize ML models: {e}")
            logger.warning("Falling back to keyword-based classification")
            self.encoder = None
            
    def _init_training_data(self):
        """Initialize training data for intent classification"""
        self.intent_examples = {
            IntentType.QUERY: [
                "What are your business hours?",
                "How do I reset my password?",
                "Can you explain this feature?",
                "What's the difference between these plans?",
                "How does billing work?",
                "Where can I find documentation?",
                "What integrations do you support?",
                "How do I contact support?",
                "What's your refund policy?",
                "Can you help me understand this error?"
            ],
            IntentType.COMPLAINT: [
                "This feature is broken and doesn't work",
                "I'm very disappointed with your service",
                "The application crashes constantly",
                "Your support team is unhelpful",
                "This is the worst experience I've had",
                "Nothing works as advertised",
                "I'm frustrated with these bugs",
                "Your product is unreliable",
                "I want to file a complaint",
                "This is completely unacceptable"
            ],
            IntentType.SERVICE_REQUEST: [
                "I need help setting up my account",
                "Can you help me configure this feature?",
                "I'd like to request a feature enhancement",
                "Please help me troubleshoot this issue",
                "I need assistance with integration",
                "Can you provide training materials?",
                "I want to upgrade my plan",
                "Please help me recover my data",
                "I need technical support",
                "Can you schedule a demo?"
            ]
        }
        
        self.urgency_examples = {
            Urgency.HIGH: [
                "urgent", "emergency", "critical", "immediately", "asap", 
                "system down", "not working", "broken", "crisis", "blocking"
            ],
            Urgency.MEDIUM: [
                "soon", "quickly", "when possible", "priority", "important",
                "affecting users", "needs attention", "moderately urgent"
            ],
            Urgency.LOW: [
                "whenever", "no rush", "low priority", "eventually", "minor",
                "nice to have", "future", "suggestion", "improvement"
            ]
        }
        
        self.sentiment_examples = {
            Sentiment.POSITIVE: [
                "great", "excellent", "amazing", "love", "perfect", "wonderful",
                "fantastic", "awesome", "satisfied", "happy", "pleased", "good"
            ],
            Sentiment.NEGATIVE: [
                "terrible", "awful", "hate", "worst", "horrible", "frustrated",
                "angry", "disappointed", "bad", "broken", "useless", "annoying"
            ],
            Sentiment.NEUTRAL: [
                "okay", "fine", "average", "normal", "standard", "regular",
                "typical", "usual", "moderate", "acceptable"
            ]
        }
        
    def _compute_training_embeddings(self):
        """Pre-compute embeddings for training examples if encoder is available"""
        if not self.encoder:
            return
            
        try:
            self.intent_embeddings = {}
            for intent, examples in self.intent_examples.items():
                embeddings = self.encoder.encode(examples)
                self.intent_embeddings[intent] = np.mean(embeddings, axis=0) #THINK
                
            logger.info("Pre-computed training embeddings successfully")
            
        except Exception as e:
            logger.error(f"Failed to compute training embeddings: {e}")
            self.encoder = None
    
    def analyze_message(self, message: str) -> IntentAnalysis:
        """
        Analyze a message to determine intent, urgency, and sentiment
        
        Args:
            message: User message to analyze
            
        Returns:
            IntentAnalysis with classified intent, urgency, sentiment, and confidence
        """
        if self.encoder:
            # Use ML-based classification
            return self._ml_classify(message)
        else:
            # Fallback to keyword-based classification
            return self._keyword_classify(message)
    
    def _ml_classify(self, message: str) -> IntentAnalysis:
        """Classify using ML models with embeddings"""
        try:
            # Encode the input message
            message_embedding = self.encoder.encode([message])[0]
            
            # Classify intent using similarity to training examples
            intent, intent_confidence = self._classify_intent_ml(message_embedding)
            
            # Classify urgency and sentiment using keyword + ML hybrid approach
            urgency = self._classify_urgency_hybrid(message)
            sentiment = self._classify_sentiment_hybrid(message)
            
            return IntentAnalysis(
                intent=intent,
                urgency=urgency,
                sentiment=sentiment,
                confidence=intent_confidence
            )
            
        except Exception as e:
            logger.error(f"ML classification failed: {e}")
            # Fallback to keyword classification
            return self._keyword_classify(message)
    
    def _classify_intent_ml(self, message_embedding: np.ndarray) -> Tuple[IntentType, float]:
        """Classify intent using cosine similarity with training embeddings"""
        similarities = {}
        
        for intent, intent_embedding in self.intent_embeddings.items():
            # Calculate cosine similarity
            similarity = np.dot(message_embedding, intent_embedding) / (
                np.linalg.norm(message_embedding) * np.linalg.norm(intent_embedding)
            )
            similarities[intent] = similarity
        
        # Find the intent with highest similarity
        best_intent = max(similarities, key=similarities.get)
        confidence = similarities[best_intent]
        
        # Ensure confidence is reasonable (between 0.3 and 1.0)
        confidence = max(0.3, min(1.0, confidence))
        
        return best_intent, confidence
    
    def _classify_urgency_hybrid(self, message: str) -> Urgency:
        """Classify urgency using hybrid keyword + context approach"""
        message_lower = message.lower()
        
        # Check for explicit urgency keywords
        for urgency, keywords in self.urgency_examples.items():
            if any(keyword in message_lower for keyword in keywords):
                return urgency
        
        # Context-based urgency detection
        if any(word in message_lower for word in ['help', 'issue', 'problem', 'error']):
            return Urgency.MEDIUM
        
        return Urgency.LOW
    
    def _classify_sentiment_hybrid(self, message: str) -> Sentiment:
        """Classify sentiment using keyword matching with context"""
        message_lower = message.lower()
        
        positive_score = sum(1 for word in self.sentiment_examples[Sentiment.POSITIVE] 
                           if word in message_lower)
        negative_score = sum(1 for word in self.sentiment_examples[Sentiment.NEGATIVE] 
                           if word in message_lower)
        
        if negative_score > positive_score:
            return Sentiment.NEGATIVE
        elif positive_score > negative_score:
            return Sentiment.POSITIVE
        else:
            return Sentiment.NEUTRAL
    
    def _keyword_classify(self, message: str) -> IntentAnalysis:
        """Fallback keyword-based classification"""
        message_lower = message.lower()
        
        # Determine intent
        intent = self._classify_intent_keywords(message_lower)
        
        # Determine urgency
        urgency = self._classify_urgency_hybrid(message_lower)
        
        # Determine sentiment
        sentiment = self._classify_sentiment_hybrid(message_lower)
        
        # Basic confidence for keyword matching
        confidence = 0.6
        
        return IntentAnalysis(
            intent=intent,
            urgency=urgency,
            sentiment=sentiment,
            confidence=confidence
        )
    
    def _classify_intent_keywords(self, message: str) -> IntentType:
        """Classify message intent using keyword matching"""
        complaint_keywords = ['complaint', 'problem', 'issue', 'bug', 'error', 'wrong', 'failed', 'broken', 'frustrated', 'disappointed']
        service_keywords = ['request', 'need', 'want', 'help', 'support', 'service', 'assistance', 'configure', 'setup']
        
        if any(keyword in message for keyword in complaint_keywords):
            return IntentType.COMPLAINT
        elif any(keyword in message for keyword in service_keywords):
            return IntentType.SERVICE_REQUEST
        else:
            return IntentType.QUERY
    
    def get_test_accuracy(self, test_cases: List[Dict[str, Any]]) -> float:
        """
        Evaluate classifier accuracy on test cases
        
        Args:
            test_cases: List of dicts with 'message' and expected 'intent', 'urgency', 'sentiment'
            
        Returns:
            Overall accuracy score (0.0 to 1.0)
        """
        if not test_cases:
            return 0.0
        
        correct_predictions = 0
        total_predictions = len(test_cases) * 3  # intent, urgency, sentiment
        
        for test_case in test_cases:
            analysis = self.analyze_message(test_case['message'])
            
            # Check intent prediction
            if analysis.intent.value == test_case.get('intent'):
                correct_predictions += 1
            
            # Check urgency prediction
            if analysis.urgency.value == test_case.get('urgency'):
                correct_predictions += 1
                
            # Check sentiment prediction
            if analysis.sentiment.value == test_case.get('sentiment'):
                correct_predictions += 1
        
        return correct_predictions / total_predictions if total_predictions > 0 else 0.0