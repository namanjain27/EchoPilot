from pydantic import BaseModel
from typing import Optional, List
from fastapi import UploadFile


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class KBUploadRequest(BaseModel):
    # Files will be handled via FastAPI Form parameters, not Pydantic model
    pass


class SessionEndRequest(BaseModel):
    session_id: str