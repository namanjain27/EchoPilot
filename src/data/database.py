"""
Database management module for EchoPilot
Handles SQLite database operations with SQLAlchemy
"""

import sqlite3
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
#from sqlalchemy.dialects.sqlite import UUID
import json
import logging

# Configure logging
logger = logging.getLogger(__name__)

Base = declarative_base()


class ChatSession(Base):
    """Chat session model for storing conversation contexts"""
    __tablename__ = 'chat_sessions'
    
    session_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_role = Column(String, nullable=False)  # 'associate' or 'customer'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(String, default='true')  # SQLite doesn't have boolean
    session_summary = Column(Text, nullable=True)
    
    # Relationships
    interactions = relationship("UserInteraction", back_populates="session", cascade="all, delete-orphan")
    tickets = relationship("Ticket", back_populates="session", cascade="all, delete-orphan")


class UserInteraction(Base):
    """User interaction model for storing chat messages and analysis"""
    __tablename__ = 'user_interactions'
    
    interaction_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey('chat_sessions.session_id'), nullable=False)
    message_role = Column(String, nullable=False)  # 'user' or 'assistant'
    message_content = Column(Text, nullable=False)
    intent_type = Column(String, nullable=True)  # 'query', 'complaint', 'service_request'
    urgency_level = Column(String, nullable=True)  # 'high', 'medium', 'low'
    sentiment_type = Column(String, nullable=True)  # 'positive', 'negative', 'neutral'
    confidence_score = Column(Float, nullable=True)
    knowledge_bases_used = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("ChatSession", back_populates="interactions")


class Ticket(Base):
    """Ticket model for storing complaint and service request tickets"""
    __tablename__ = 'tickets'
    
    ticket_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey('chat_sessions.session_id'), nullable=False)
    ticket_type = Column(String, nullable=False)  # 'complaint', 'service_request', 'feature_request'
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String, default='open')  # 'open', 'in_progress', 'resolved', 'closed'
    priority = Column(String, default='medium')  # 'high', 'medium', 'low'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    jira_ticket_id = Column(String, nullable=True)  # Reference to external Jira ticket
    
    # Relationships
    session = relationship("ChatSession", back_populates="tickets")


class DatabaseManager:
    """Database manager for handling all database operations"""
    
    def __init__(self, db_path: str = "echopilot.db"):
        """
        Initialize database manager
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables if they don't exist
        self._create_tables()
        
    def _create_tables(self):
        """Create all database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    def get_session(self) -> Session:
        """Get a database session"""
        return self.SessionLocal()
    
    def close_session(self, session: Session):
        """Close a database session"""
        session.close()
    
    # Chat Session Operations
    def create_chat_session(self, user_role: str) -> ChatSession:
        """
        Create a new chat session
        
        Args:
            user_role: Role of the user ('associate' or 'customer')
            
        Returns:
            Created ChatSession object
        """
        session = self.get_session()
        try:
            chat_session = ChatSession(user_role=user_role)
            session.add(chat_session)
            session.commit()
            session.refresh(chat_session)
            logger.info(f"Created chat session: {chat_session.session_id}")
            return chat_session
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create chat session: {e}")
            raise
        finally:
            self.close_session(session)
    
    def get_chat_session(self, session_id: str) -> Optional[ChatSession]:
        """
        Get a chat session by ID
        
        Args:
            session_id: Session ID to lookup
            
        Returns:
            ChatSession object or None if not found
        """
        session = self.get_session()
        try:
            chat_session = session.query(ChatSession).filter(ChatSession.session_id == session_id).first()
            return chat_session
        except Exception as e:
            logger.error(f"Failed to get chat session {session_id}: {e}")
            return None
        finally:
            self.close_session(session)
    
    def update_chat_session(self, session_id: str, **kwargs) -> bool:
        """
        Update a chat session
        
        Args:
            session_id: Session ID to update
            **kwargs: Fields to update
            
        Returns:
            True if successful, False otherwise
        """
        session = self.get_session()
        try:
            chat_session = session.query(ChatSession).filter(ChatSession.session_id == session_id).first()
            if chat_session:
                for key, value in kwargs.items():
                    if hasattr(chat_session, key):
                        setattr(chat_session, key, value)
                chat_session.updated_at = datetime.utcnow()
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update chat session {session_id}: {e}")
            return False
        finally:
            self.close_session(session)
    
    # User Interaction Operations
    def add_interaction(self, session_id: str, message_role: str, message_content: str, 
                       intent_analysis: Optional[Dict[str, Any]] = None, 
                       knowledge_bases_used: Optional[List[str]] = None) -> UserInteraction:
        """
        Add a user interaction to the database
        
        Args:
            session_id: Session ID this interaction belongs to
            message_role: Role of the message sender ('user' or 'assistant')
            message_content: Content of the message
            intent_analysis: Optional intent analysis results
            knowledge_bases_used: Optional list of knowledge bases used
            
        Returns:
            Created UserInteraction object
        """
        session = self.get_session()
        try:
            interaction = UserInteraction(
                session_id=session_id,
                message_role=message_role,
                message_content=message_content
            )
            
            # Add intent analysis if provided
            if intent_analysis:
                interaction.intent_type = intent_analysis.get('intent')
                interaction.urgency_level = intent_analysis.get('urgency')
                interaction.sentiment_type = intent_analysis.get('sentiment')
                interaction.confidence_score = intent_analysis.get('confidence')
            
            # Add knowledge bases used if provided
            if knowledge_bases_used:
                interaction.knowledge_bases_used = json.dumps(knowledge_bases_used)
            
            session.add(interaction)
            session.commit()
            session.refresh(interaction)
            logger.info(f"Added interaction: {interaction.interaction_id}")
            return interaction
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to add interaction: {e}")
            raise
        finally:
            self.close_session(session)
    
    def get_session_interactions(self, session_id: str) -> List[UserInteraction]:
        """
        Get all interactions for a session
        
        Args:
            session_id: Session ID to get interactions for
            
        Returns:
            List of UserInteraction objects
        """
        session = self.get_session()
        try:
            interactions = session.query(UserInteraction).filter(
                UserInteraction.session_id == session_id
            ).order_by(UserInteraction.created_at).all()
            return interactions
        except Exception as e:
            logger.error(f"Failed to get interactions for session {session_id}: {e}")
            return []
        finally:
            self.close_session(session)
    
    # Ticket Operations
    def create_ticket(self, session_id: str, ticket_type: str, title: str, 
                     description: str, priority: str = 'medium') -> Ticket:
        """
        Create a new ticket
        
        Args:
            session_id: Session ID this ticket belongs to
            ticket_type: Type of ticket ('complaint', 'service_request', 'feature_request')
            title: Ticket title
            description: Ticket description
            priority: Ticket priority ('high', 'medium', 'low')
            
        Returns:
            Created Ticket object
        """
        session = self.get_session()
        try:
            ticket = Ticket(
                session_id=session_id,
                ticket_type=ticket_type,
                title=title,
                description=description,
                priority=priority
            )
            session.add(ticket)
            session.commit()
            session.refresh(ticket)
            logger.info(f"Created ticket: {ticket.ticket_id}")
            return ticket
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create ticket: {e}")
            raise
        finally:
            self.close_session(session)
    
    def get_ticket(self, ticket_id: str) -> Optional[Ticket]:
        """
        Get a ticket by ID
        
        Args:
            ticket_id: Ticket ID to lookup
            
        Returns:
            Ticket object or None if not found
        """
        session = self.get_session()
        try:
            ticket = session.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
            return ticket
        except Exception as e:
            logger.error(f"Failed to get ticket {ticket_id}: {e}")
            return None
        finally:
            self.close_session(session)
    
    def update_ticket_status(self, ticket_id: str, status: str, jira_ticket_id: Optional[str] = None) -> bool:
        """
        Update ticket status
        
        Args:
            ticket_id: Ticket ID to update
            status: New status ('open', 'in_progress', 'resolved', 'closed')
            jira_ticket_id: Optional Jira ticket ID reference
            
        Returns:
            True if successful, False otherwise
        """
        session = self.get_session()
        try:
            ticket = session.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
            if ticket:
                ticket.status = status
                ticket.updated_at = datetime.utcnow()
                if jira_ticket_id:
                    ticket.jira_ticket_id = jira_ticket_id
                if status in ['resolved', 'closed']:
                    ticket.resolved_at = datetime.utcnow()
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update ticket {ticket_id}: {e}")
            return False
        finally:
            self.close_session(session)
    
    def get_session_tickets(self, session_id: str) -> List[Ticket]:
        """
        Get all tickets for a session
        
        Args:
            session_id: Session ID to get tickets for
            
        Returns:
            List of Ticket objects
        """
        session = self.get_session()
        try:
            tickets = session.query(Ticket).filter(
                Ticket.session_id == session_id
            ).order_by(Ticket.created_at).all()
            return tickets
        except Exception as e:
            logger.error(f"Failed to get tickets for session {session_id}: {e}")
            return []
        finally:
            self.close_session(session)
    
    # Utility Operations
    def get_database_stats(self) -> Dict[str, int]:
        """
        Get database statistics
        
        Returns:
            Dictionary with counts of sessions, interactions, and tickets
        """
        session = self.get_session()
        try:
            stats = {
                'total_sessions': session.query(ChatSession).count(),
                'active_sessions': session.query(ChatSession).filter(ChatSession.is_active == 'true').count(),
                'total_interactions': session.query(UserInteraction).count(),
                'total_tickets': session.query(Ticket).count(),
                'open_tickets': session.query(Ticket).filter(Ticket.status == 'open').count()
            }
            return stats
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}
        finally:
            self.close_session(session)