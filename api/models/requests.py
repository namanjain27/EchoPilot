from pydantic import BaseModel
from typing import Optional, List
from fastapi import UploadFile
from enum import Enum


class UserRole(str, Enum):
    """Enumeration of user roles for RBAC"""
    CUSTOMER = "customer"
    VENDOR = "vendor"
    ASSOCIATE = "associate"
    LEADERSHIP = "leadership"
    HR = "hr"


class DocumentVisibility(str, Enum):
    """Enumeration of document visibility levels"""
    PUBLIC = "Public"
    PRIVATE = "Private"
    RESTRICTED = "Restricted"


class TenantRequest(BaseModel):
    """Base class for tenant-aware requests"""
    tenant_id: str = "default"
    user_role: UserRole = UserRole.CUSTOMER


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatRequestWithTenant(TenantRequest):
    """Chat request with tenant context"""
    message: str
    session_id: Optional[str] = None


class KBUploadRequest(BaseModel):
    # Files will be handled via FastAPI Form parameters, not Pydantic model
    pass


class KBUploadRequestWithTenant(BaseModel):
    """Knowledge base upload request with tenant and RBAC context"""
    tenant_id: str = "default"
    access_roles: List[UserRole] = [UserRole.CUSTOMER]
    document_visibility: DocumentVisibility = DocumentVisibility.PUBLIC


class SessionEndRequest(BaseModel):
    session_id: str