from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ChatResponse(BaseModel):
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