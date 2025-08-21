"""
Integrations module for EchoPilot
"""

from .ticket_manager import TicketManager, Ticket, TicketType, TicketStatus
from .jira_client import JiraClient

__all__ = ['TicketManager', 'Ticket', 'TicketType', 'TicketStatus', 'JiraClient']