from fastapi import APIRouter, HTTPException
import uuid
from datetime import datetime
from typing import Dict, Any

from ..models.requests import SessionEndRequest
from ..models.responses import SessionEndResponse, SessionStartResponse, SessionHistoryResponse, SessionClearResponse
from echo_ui import initialize_agent, save_current_chat_session, clear_chat_session

router = APIRouter(prefix="/api/v1", tags=["session"])

# In-memory session storage
sessions: Dict[str, Dict[str, Any]] = {}


@router.post("/session/start", response_model=SessionStartResponse)
async def start_session():
    """
    Initialize new chat session
    Function Mapping: echo_ui.initialize_agent() + session management
    """
    try:
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Initialize agent
        agent_initialized = False
        try:
            initialize_agent()
            agent_initialized = True
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Agent initialization failed: {str(e)}")
        
        # Create new session
        sessions[session_id] = {
            "messages": [],
            "created_at": datetime.now(),
            "agent_initialized": agent_initialized
        }
        
        return SessionStartResponse(
            session_id=session_id,
            agent_initialized=agent_initialized,
            timestamp=datetime.now()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start session: {str(e)}")


@router.post("/session/end", response_model=SessionEndResponse)
async def end_session(request: SessionEndRequest):
    """
    End and save chat session
    Function Mapping: echo_ui.save_current_chat_session()
    """
    try:
        session_id = request.session_id
        
        # Check if session exists
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Save current chat session
        save_current_chat_session()
        
        # Remove session from memory
        del sessions[session_id]
        
        return SessionEndResponse(
            success=True,
            message="Session ended and saved successfully",
            session_id=session_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to end session: {str(e)}")


@router.get("/session/history", response_model=SessionHistoryResponse)
async def get_session_history(session_id: str):
    """
    Get current session messages
    Function Mapping: echo_ui.get_current_chat_messages()
    """
    try:
        # Check if session exists
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_data = sessions[session_id]
        messages = session_data.get("messages", [])
        
        # Transform messages to API-friendly format
        api_messages = []
        for msg in messages:
            api_messages.append({
                "role": msg.get("role", "unknown"),
                "content": msg.get("content", ""),
                "timestamp": msg.get("timestamp", datetime.now().isoformat())
            })
        
        return SessionHistoryResponse(
            session_id=session_id,
            messages=api_messages,
            message_count=len(api_messages)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session history: {str(e)}")


@router.delete("/session/clear", response_model=SessionClearResponse)
async def clear_session(session_id: str):
    """
    Clear current session without saving
    Function Mapping: echo_ui.clear_chat_session()
    """
    try:
        # Check if session exists
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Clear chat session using echo_ui function
        clear_chat_session()
        
        # Remove session from memory without saving
        del sessions[session_id]
        
        return SessionClearResponse(
            success=True,
            session_id=session_id,
            message="Session cleared successfully without saving"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear session: {str(e)}")