"""
Session management module for EchoPilot
Handles session state and user context persistence with role-based chat separation
"""

import streamlit as st
from typing import Dict, Any, Optional, List
from .role_manager import UserRole, RoleManager


class SessionHandler:
    """Manages user session state and context with role-separated chat histories"""
    
    def __init__(self):
        self.role_manager = RoleManager()
        self._initialize_session_state()
    
    def _initialize_session_state(self) -> None:
        """Initialize session state variables with role-based chat storage"""
        if 'user_role' not in st.session_state:
            st.session_state.user_role = None
        
        # Initialize role-based chat histories instead of single chat_history
        if 'chat_histories' not in st.session_state:
            st.session_state.chat_histories = {
                "associate": [],
                "customer": []
            }
        
        # Migrate old single chat_history to role-based system if it exists
        if 'chat_history' in st.session_state and st.session_state.chat_history:
            # Move existing chat to customer role as default migration
            if not st.session_state.chat_histories["customer"]:
                st.session_state.chat_histories["customer"] = st.session_state.chat_history
            # Remove old single chat_history
            del st.session_state.chat_history
        
        if 'session_id' not in st.session_state:
            st.session_state.session_id = None
    
    def set_user_role(self, role: Optional[UserRole]) -> None:
        """Set user role in session and role manager"""
        st.session_state.user_role = role
        self.role_manager.set_role(role)
    
    def get_user_role(self) -> Optional[UserRole]:
        """Get current user role from session"""
        return st.session_state.user_role
    
    def get_chat_history(self, role: Optional[UserRole] = None) -> List[Dict]:
        """Get chat history for specific role or current role if none specified"""
        if role is None:
            role = self.get_user_role()
        
        if role is None:
            # Default to customer role if no role is set
            role_key = "customer"
        else:
            role_key = role.value
        
        return st.session_state.chat_histories.get(role_key, [])
    
    def add_message(self, message: Dict[str, Any], role: Optional[UserRole] = None) -> None:
        """Add message to role-specific chat history"""
        if role is None:
            role = self.get_user_role()
        
        if role is None:
            # Default to customer role if no role is set
            role_key = "customer"
        else:
            role_key = role.value
        
        if role_key not in st.session_state.chat_histories:
            st.session_state.chat_histories[role_key] = []
        
        st.session_state.chat_histories[role_key].append(message)
    
    def clear_chat_history(self, role: Optional[UserRole] = None) -> None:
        """Clear chat history for specific role or current role if none specified"""
        if role is None:
            role = self.get_user_role()
        
        if role is None:
            # Default to customer role if no role is set
            role_key = "customer"
        else:
            role_key = role.value
        
        if role_key in st.session_state.chat_histories:
            st.session_state.chat_histories[role_key] = []
    
    # Convenience methods for current role operations
    def get_current_role_chat_history(self) -> List[Dict]:
        """Get chat history for the current user role"""
        return self.get_chat_history()
    
    def add_message_for_current_role(self, message: Dict[str, Any]) -> None:
        """Add message to current role's chat history"""
        self.add_message(message)
    
    def clear_current_role_chat_history(self) -> None:
        """Clear current role's chat history"""
        self.clear_chat_history()
    
    # Additional utility methods
    def clear_all_chat_histories(self) -> None:
        """Clear all chat histories for both roles"""
        st.session_state.chat_histories = {
            "associate": [],
            "customer": []
        }
    
    def get_role_manager(self) -> RoleManager:
        """Get the role manager instance"""
        return self.role_manager