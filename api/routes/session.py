from fastapi import APIRouter, HTTPException
import uuid
from datetime import datetime
from typing import Dict, Any

from ..models.requests import SessionEndRequest
from ..models.responses import SessionEndResponse, SessionStartResponse
from echo_ui import initialize_agent, save_current_chat_session

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