"""
Role management module for EchoPilot
Handles user role selection and access control
"""

from enum import Enum
from typing import List, Optional


class UserRole(Enum):
    """User role types"""
    ASSOCIATE = "associate"
    CUSTOMER = "customer"


class RoleManager:
    """Manages user roles and access permissions"""
    
    def __init__(self):
        self.current_role: Optional[UserRole] = None
    
    def set_role(self, role: UserRole) -> None:
        """Set the current user role"""
        self.current_role = role
    
    def get_role(self) -> Optional[UserRole]:
        """Get the current user role"""
        return self.current_role
    
    def has_access_to_internal_kb(self) -> bool:
        """Check if current role has access to internal knowledge base"""
        return self.current_role == UserRole.ASSOCIATE
    
    def get_accessible_knowledge_bases(self) -> List[str]:
        """Get list of knowledge bases accessible to current role"""
        accessible_kbs = ["general"]  # General KB accessible to all
        
        if self.current_role == UserRole.ASSOCIATE:
            accessible_kbs.append("internal")  # Internal KB only for associates
        
        return accessible_kbs