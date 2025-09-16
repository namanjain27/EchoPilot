from fastapi import APIRouter, HTTPException
import uuid
from datetime import datetime
from typing import Dict, Any

from ..models.requests import SessionEndRequest
from ..models.responses import SessionEndResponse, SessionStartResponse, SessionHistoryResponse, SessionClearResponse
from ..dependencies import get_or_create_session, get_session_messages, clear_session, _sessions
from echo_ui import initialize_agent, save_current_chat_session, clear_chat_session

router = APIRouter(prefix="/api/v1", tags=["session"])


@router.post("/session/start", response_model=SessionStartResponse)
async def start_session():
    """
    Initialize new chat session
    Function Mapping: echo_ui.initialize_agent() + session management
    """
    try:
        # Initialize agent
        agent_initialized = False
        try:
            initialize_agent()
            agent_initialized = True
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Agent initialization failed: {str(e)}")
        
        # Create new session using dependencies
        session_id = get_or_create_session()
        
        # Add agent initialization status to session
        if session_id in _sessions:
            _sessions[session_id]["agent_initialized"] = agent_initialized
        
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
        if session_id not in _sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Save current chat session
        save_current_chat_session()
        
        # Remove session from memory
        del _sessions[session_id]
        
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
        if session_id not in _sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get messages from dependencies session storage
        messages = get_session_messages(session_id)
        
        # Transform messages to API-friendly format
        api_messages = []
        for msg in messages:
            # Handle different message types (HumanMessage, AIMessage, etc.)
            if hasattr(msg, 'type') and hasattr(msg, 'content'):
                role = "user" if msg.type == "human" else "assistant"
                content = msg.content
            else:
                # Fallback for dict-like messages
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
            
            api_messages.append({
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat()
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
async def clear_session_endpoint(session_id: str):
    """
    Clear current session without saving
    Function Mapping: echo_ui.clear_chat_session()
    """
    try:
        # Check if session exists
        if session_id not in _sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Clear chat session using dependencies function
        clear_session(session_id)
        
        return SessionClearResponse(
            success=True,
            session_id=session_id,
            message="Session cleared successfully without saving"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear session: {str(e)}")