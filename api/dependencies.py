import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from langchain_core.messages import BaseMessage

# In-memory session storage
_sessions: Dict[str, Dict] = {}

def get_or_create_session(session_id: Optional[str] = None) -> str:
    """Get existing session or create new one"""
    if session_id and session_id in _sessions:
        return session_id
    
    # Create new session
    new_session_id = str(uuid.uuid4())
    _sessions[new_session_id] = {
        "messages": [],
        "created_at": datetime.now(),
        "last_activity": datetime.now()
    }
    return new_session_id

def get_session_messages(session_id: str) -> List[BaseMessage]:
    """Get messages for a session"""
    if session_id in _sessions:
        return _sessions[session_id]["messages"].copy()
    return []

def add_session_message(session_id: str, message: BaseMessage):
    """Add message to session"""
    if session_id in _sessions:
        _sessions[session_id]["messages"].append(message)
        _sessions[session_id]["last_activity"] = datetime.now()

def clear_session(session_id: str):
    """Clear session messages"""
    if session_id in _sessions:
        _sessions[session_id]["messages"].clear()
        _sessions[session_id]["last_activity"] = datetime.now()

def cleanup_old_sessions():
    """Remove sessions older than 24 hours"""
    cutoff_time = datetime.now() - timedelta(hours=24)
    sessions_to_remove = [
        sid for sid, session in _sessions.items() 
        if session["last_activity"] < cutoff_time
    ]
    for sid in sessions_to_remove:
        del _sessions[sid]