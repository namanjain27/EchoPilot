"""
Session management module for EchoPilot
Handles session state and user context persistence
"""

import streamlit as st
from typing import Dict, Any, Optional
from .role_manager import UserRole, RoleManager


class SessionHandler:
    """Manages user session state and context"""
    
    def __init__(self):
        self.role_manager = RoleManager()
        self._initialize_session_state()
    
    def _initialize_session_state(self) -> None:
        """Initialize session state variables"""
        if 'user_role' not in st.session_state:
            st.session_state.user_role = None
        
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        if 'session_id' not in st.session_state:
            st.session_state.session_id = None
    
    def set_user_role(self, role: UserRole) -> None:
        """Set user role in session and role manager"""
        st.session_state.user_role = role
        self.role_manager.set_role(role)
    
    def get_user_role(self) -> Optional[UserRole]:
        """Get current user role from session"""
        return st.session_state.user_role
    
    def add_message(self, message: Dict[str, Any]) -> None:
        """Add message to chat history"""
        st.session_state.chat_history.append(message)
    
    def get_chat_history(self) -> list:
        """Get current chat history"""
        return st.session_state.chat_history
    
    def clear_chat_history(self) -> None:
        """Clear current chat history"""
        st.session_state.chat_history = []
    
    def get_role_manager(self) -> RoleManager:
        """Get the role manager instance"""
        return self.role_manager