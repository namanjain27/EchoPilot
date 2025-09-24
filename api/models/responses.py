from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class TenantAwareResponse(BaseModel):
    """Base response class with tenant validation info"""
    tenant_id: str
    access_validated: bool = True


class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: datetime
    files_processed: int = 0


class ChatResponseWithTenant(TenantAwareResponse):
    """Chat response with tenant context"""
    response: str
    session_id: str
    timestamp: datetime
    files_processed: int = 0


class KBUploadResponse(BaseModel):
    success: bool
    files_processed: int
    chunks_created: int
    errors: List[str] = []
    details: List[dict] = []


class KBUploadResponseWithTenant(TenantAwareResponse):
    """Knowledge base upload response with tenant context"""
    success: bool
    files_processed: int
    chunks_created: int
    errors: List[str] = []
    details: List[dict] = []


class SessionEndResponse(BaseModel):
    success: bool
    message: str
    session_id: str


class KBStatusResponse(BaseModel):
    status: str  # "ready", "empty", "error"
    document_count: int
    collection_name: str
    error_message: Optional[str] = None


class KBStatusResponseWithTenant(TenantAwareResponse):
    """Knowledge base status response with tenant context"""
    status: str  # "ready", "empty", "error"
    document_count: int
    collection_name: str
    error_message: Optional[str] = None


class SessionStartResponse(BaseModel):
    session_id: str
    agent_initialized: bool
    timestamp: datetime


class SessionHistoryResponse(BaseModel):
    session_id: str
    messages: List[dict]
    message_count: int


class SessionClearResponse(BaseModel):
    success: bool
    session_id: str
    message: str