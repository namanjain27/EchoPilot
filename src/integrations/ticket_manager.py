"""
Ticket management module for EchoPilot
Handles ticket creation, tracking, and status management
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass


class TicketType(Enum):
    """Types of tickets"""
    COMPLAINT = "complaint"
    SERVICE_REQUEST = "service_request"
    FEATURE_REQUEST = "feature_request"


class TicketStatus(Enum):
    """Ticket status types"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


@dataclass
class Ticket:
    """Ticket data structure"""
    ticket_id: str
    ticket_type: TicketType
    title: str
    description: str
    status: TicketStatus
    created_at: datetime
    user_role: str
    urgency: str
    sentiment: str


class TicketManager:
    """Manages ticket creation and tracking"""
    
    def __init__(self):
        self.tickets: Dict[str, Ticket] = {}
    
    def create_ticket(self, ticket_data: Dict[str, Any]) -> str:
        """
        Create a new ticket
        
        Args:
            ticket_data: Dictionary containing ticket information
            
        Returns:
            Generated ticket ID
        """
        ticket_id = self._generate_ticket_id()
        
        ticket = Ticket(
            ticket_id=ticket_id,
            ticket_type=TicketType(ticket_data.get('type', 'complaint')),
            title=ticket_data.get('title', 'No title provided'),
            description=ticket_data.get('description', ''),
            status=TicketStatus.OPEN,
            created_at=datetime.now(),
            user_role=ticket_data.get('user_role', 'customer'),
            urgency=ticket_data.get('urgency', 'medium'),
            sentiment=ticket_data.get('sentiment', 'neutral')
        )
        
        self.tickets[ticket_id] = ticket
        
        return ticket_id
    
    def get_ticket(self, ticket_id: str) -> Optional[Ticket]:
        """Get ticket by ID"""
        return self.tickets.get(ticket_id)
    
    def update_ticket_status(self, ticket_id: str, status: TicketStatus) -> bool:
        """Update ticket status"""
        if ticket_id in self.tickets:
            self.tickets[ticket_id].status = status
            return True
        return False
    
    def _generate_ticket_id(self) -> str:
        """Generate unique ticket ID"""
        return f"EP-{uuid.uuid4().hex[:8].upper()}"
    
    def get_ticket_summary(self, ticket_id: str) -> Dict[str, Any]:
        """Get ticket summary for reference"""
        ticket = self.get_ticket(ticket_id)
        if not ticket:
            return {}
        
        return {
            "ticket_id": ticket.ticket_id,
            "type": ticket.ticket_type.value,
            "title": ticket.title,
            "status": ticket.status.value,
            "created_at": ticket.created_at.isoformat(),
            "urgency": ticket.urgency
        }