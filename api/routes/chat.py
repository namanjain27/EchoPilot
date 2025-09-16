from fastapi import APIRouter, HTTPException, Form, UploadFile, File
from typing import Optional, List
from datetime import datetime
import tempfile
import os
import uuid

from ..models.requests import ChatRequest
from ..models.responses import ChatResponse
from ..dependencies import get_or_create_session, add_session_message
from echo_ui import initialize_agent, process_user_message
from multiModalInputService import process_uploaded_files
from langchain_core.messages import HumanMessage, AIMessage

router = APIRouter(prefix="/api/v1", tags=["chat"])

# Global agent initialization
_agent_initialized = False

def ensure_agent_initialized():
    """Ensure agent is initialized globally"""
    global _agent_initialized
    if not _agent_initialized:
        try:
            initialize_agent()
            _agent_initialized = True
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Agent initialization failed: {str(e)}")

@router.post("/chat", response_model=ChatResponse)
async def chat(
    message: str = Form(...),
    session_id: Optional[str] = Form(None),
    files: List[UploadFile] = File(default=[])
):
    """
    Process user query with optional file attachments
    """
    try:
        # Ensure agent is ready
        ensure_agent_initialized()
        
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
        
        # Process message through agent
        ai_response = process_user_message(message, processed_files)
        
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