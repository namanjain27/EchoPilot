from fastapi import APIRouter, HTTPException, Form, UploadFile, File
from typing import Optional, List
from datetime import datetime
import tempfile
import os
import uuid

from ..models.requests import ChatRequest, ChatRequestWithTenant, UserRole
from ..models.responses import ChatResponse, ChatResponseWithTenant
from ..dependencies import get_or_create_session, add_session_message
from echo_ui import initialize_agent, process_user_message
from multiModalInputService import process_uploaded_files
from langchain_core.messages import HumanMessage, AIMessage

router = APIRouter(prefix="/api/v1", tags=["chat"])

# Global agent initialization - now supports tenant context
_agent_initialized = False
_current_agent_context = {"tenant_id": "default", "user_role": "customer"}

def ensure_agent_initialized(tenant_id: str = "default", user_role: str = "customer"):
    """Ensure agent is initialized with proper tenant context"""
    global _agent_initialized, _current_agent_context

    # Check if we need to reinitialize due to context change
    context_changed = (
        _current_agent_context["tenant_id"] != tenant_id or
        _current_agent_context["user_role"] != user_role
    )

    if not _agent_initialized or context_changed:
        try:
            initialize_agent(tenant_id=tenant_id, user_role=user_role)
            _agent_initialized = True
            _current_agent_context = {"tenant_id": tenant_id, "user_role": user_role}
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Agent initialization failed: {str(e)}")

@router.post("/chat", response_model=ChatResponse)
async def chat(
    message: str = Form(...),
    session_id: Optional[str] = Form(None),
    files: List[UploadFile] = File(default=[])
):
    """
    Process user query with optional file attachments (legacy endpoint)
    """
    return await _process_chat_request(message, session_id, files)

@router.post("/chat-tenant", response_model=ChatResponseWithTenant)
async def chat_with_tenant(
    message: str = Form(...),
    tenant_id: str = Form(default="default"),
    user_role: str = Form(default="customer"),
    session_id: Optional[str] = Form(None),
    files: List[UploadFile] = File(default=[])
):
    """
    Process user query with tenant context and optional file attachments
    """
    # Validate user role
    try:
        UserRole(user_role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid user_role. Must be one of: {[r.value for r in UserRole]}")

    # Process chat with tenant context
    chat_result = await _process_chat_request(message, session_id, files, tenant_id=tenant_id, user_role=user_role)

    return ChatResponseWithTenant(
        tenant_id=tenant_id,
        access_validated=True,
        response=chat_result.response,
        session_id=chat_result.session_id,
        timestamp=chat_result.timestamp,
        files_processed=chat_result.files_processed
    )

async def _process_chat_request(
    message: str,
    session_id: Optional[str],
    files: List[UploadFile],
    tenant_id: str = "default",
    user_role: str = "customer"
) -> ChatResponse:
    """
    Common chat processing logic with tenant context support
    """
    try:
        # Ensure agent is ready with tenant context
        ensure_agent_initialized(tenant_id=tenant_id, user_role=user_role)

        # Get or create session
        actual_session_id = get_or_create_session(session_id)

        # Process uploaded files if any
        processed_files = None
        files_processed_count = 0

        if files:
            # Convert UploadFile objects to format expected by process_uploaded_files
            uploaded_files_list = []
            for file in files:
                # Create a temporary object that mimics Streamlit's UploadedFile
                class MockUploadedFile:
                    def __init__(self, upload_file: UploadFile):
                        self.name = upload_file.filename
                        self.type = upload_file.content_type
                        self._content = None
                        self._upload_file = upload_file

                    def getvalue(self):
                        if self._content is None:
                            self._content = self._upload_file.file.read()
                            self._upload_file.file.seek(0)  # Reset file pointer
                        return self._content

                uploaded_files_list.append(MockUploadedFile(file))

            processed_files = process_uploaded_files(uploaded_files_list)
            files_processed_count = len(processed_files.get("image_files", [])) + len(processed_files.get("doc_files", []))

        # Store user message in session
        user_message = HumanMessage(content=message)
        add_session_message(actual_session_id, user_message)

        # Process message through agent with tenant context
        ai_response = process_user_message(
            message,
            processed_files,
            tenant_id=tenant_id,
            user_role=user_role
        )

        # Store AI response in session
        ai_message = AIMessage(content=ai_response)
        add_session_message(actual_session_id, ai_message)

        return ChatResponse(
            response=ai_response,
            session_id=actual_session_id,
            timestamp=datetime.now(),
            files_processed=files_processed_count
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")