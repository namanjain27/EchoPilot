# Goal
we need to expose the APIs to apply any tenant to use the service.
Ensure that the existing UI interface and its functioning remain unaffected.

# APIs for:
1. POST: to get agent response from user query with files
2. POST: uploading files to KB 
3. End session
4. get number of uploaded docs


  Core APIs:
  1. POST /api/v1/chat - Process user query with
  optional files
  2. POST /api/v1/knowledge-base/upload - Upload files     
  to knowledge base
  3. POST /api/v1/session/end - End and save chat
  session
  4. GET /api/v1/knowledge-base/status - Get KB stats      
  and document count

  Additional Essential APIs:
  5. POST /api/v1/session/start - Initialize new chat      
  session
  6. GET /api/v1/session/history - Get current session     
  messages
  7. DELETE /api/v1/session/clear - Clear current
  session without saving
  8. GET /api/v1/health - API health check


  2. Authentication & Multi-tenancy [FUTURE]
  Since you mentioned "any tenant to use the service":     
  - Add API key authentication middleware
  - Include tenant_id in request headers/body
  - Isolate vector store collections per tenant
  - Rate limiting per tenant

# Implementation Plan

## File Structure
```
api/
├── __init__.py
├── main.py              # FastAPI app initialization
├── routes/
│   ├── __init__.py
│   ├── chat.py          # Chat endpoints  
│   ├── knowledge_base.py # KB management
│   └── session.py       # Session management
├── models/
│   ├── __init__.py
│   ├── requests.py      # Pydantic request models
│   └── responses.py     # Pydantic response models
└── dependencies.py      # FastAPI dependencies
```

## API Implementation Mapping

### 1. POST /api/v1/chat
**Function Mapping:** `echo_ui.process_user_message()` + `multiModalInputService.process_uploaded_files()`
**Request Model:**
```python
class ChatRequest(BaseModel):
    message: str
    files: Optional[List[UploadFile]] = None
    session_id: Optional[str] = None
```
**Response Model:**
```python
class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: datetime
    files_processed: int = 0
```
**Implementation:**
- Use `process_uploaded_files()` to handle file attachments
- Call `process_user_message(message, processed_files)` 
- Generate/track session_id for chat continuity
- Return AI response with metadata

### 2. POST /api/v1/knowledge-base/upload  
**Function Mapping:** `data_ingestion.ingest_file_with_feedback()`
**Request Model:**
```python
class KBUploadRequest(BaseModel):
    files: List[UploadFile]
```
**Response Model:**
```python
class KBUploadResponse(BaseModel):
    success: bool
    files_processed: int
    chunks_created: int
    errors: List[str] = []
    details: List[dict] = []
```
**Implementation:**
- Save uploaded files to temp directory
- Call `ingest_file_with_feedback()` for each file
- Aggregate results and return comprehensive status

### 3. POST /api/v1/session/end
**Function Mapping:** `echo_ui.save_current_chat_session()`
**Request Model:**
```python
class SessionEndRequest(BaseModel):
    session_id: str
```
**Response Model:**
```python
class SessionEndResponse(BaseModel):
    success: bool
    message: str
    session_id: str
```
**Implementation:**
- Call `save_current_chat_session()` to persist chat
- Clear session from memory
- Return confirmation

### 4. GET /api/v1/knowledge-base/status
**Function Mapping:** `echo_ui.get_vector_store_status()`
**Response Model:**
```python
class KBStatusResponse(BaseModel):
    status: str  # "ready", "empty", "error"
    document_count: int
    collection_name: str
    error_message: Optional[str] = None
```
**Implementation:**
- Direct call to `get_vector_store_status()`
- Return vector store statistics

### 5. POST /api/v1/session/start
**Function Mapping:** `echo_ui.initialize_agent()` + session management
**Response Model:**
```python
class SessionStartResponse(BaseModel):
    session_id: str
    agent_initialized: bool
    timestamp: datetime
```
**Implementation:**
- Call `initialize_agent()` to ensure agent ready
- Generate unique session_id (UUID)
- Initialize empty chat history for session
- Return session details

### 6. GET /api/v1/session/history
**Function Mapping:** `echo_ui.get_current_chat_messages()`
**Request Parameters:**
```python
session_id: str (query parameter)
```
**Response Model:**
```python
class SessionHistoryResponse(BaseModel):
    session_id: str
    messages: List[dict]
    message_count: int
```
**Implementation:**
- Retrieve chat history for given session_id
- Transform messages to API-friendly format
- Return conversation history

### 7. DELETE /api/v1/session/clear
**Function Mapping:** `echo_ui.clear_chat_session()`
**Request Parameters:**
```python
session_id: str (query parameter)
```
**Response Model:**
```python
class SessionClearResponse(BaseModel):
    success: bool
    session_id: str
    message: str
```
**Implementation:**
- Call `clear_chat_session()` for given session
- Remove session from memory without saving
- Return confirmation

### 8. GET /api/v1/health
**Function Mapping:** Custom health check
**Response Model:**
```python
class HealthResponse(BaseModel):
    status: str  # "healthy", "unhealthy"
    timestamp: datetime
    services: dict  # {"agent": bool, "vector_store": bool, "api_key": bool}
```
**Implementation:**
- Check if agent can be initialized
- Verify vector store connectivity
- Validate API key presence
- Return system health status

## Session Management Strategy
- Use in-memory dictionary to store session data: `{session_id: {"messages": [], "created_at": datetime}}`
- Session cleanup after 24 hours of inactivity
- Global agent instance shared across all sessions
- Individual chat history per session

## Error Handling Standards
- HTTP 400: Bad Request (invalid input)
- HTTP 422: Validation Error (Pydantic validation)
- HTTP 500: Internal Server Error (processing failures)
- HTTP 503: Service Unavailable (agent initialization fails)

## File Handling
- Temporary file storage for uploads
- Automatic cleanup after processing
- Size limits: 10MB per file, 5 files max per request
- Supported formats: PDF, DOCX, TXT, MD, PNG, JPG, JPEG, GIF, WEBP

## Dependencies Required
```python
fastapi>=0.104.0
uvicorn>=0.24.0
python-multipart>=0.0.6  # For file uploads
pydantic>=2.0.0
```
