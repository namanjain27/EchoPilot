"""
Authentication module for EchoPilot
"""

from .role_manager import RoleManager, UserRole
from .session_handler import SessionHandler

__all__ = ['RoleManager', 'UserRole', 'SessionHandler']