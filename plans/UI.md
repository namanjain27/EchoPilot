# EchoPilot UI Implementation Plan

## Overview
Create a clean Streamlit interface for EchoPilot with two main sections:
1. **Data Ingestion Section** - File upload and management for knowledge base
2. **Chat Section** - Interactive chat with multi-modal input support

## UI Architecture

### Main Layout Structure
```
┌─────────────────────────────────────────┐
│              EchoPilot                  │
│        Customer Success Copilot         │
├─────────────────────────────────────────┤
│  [Data Ingestion] | [Chat Interface]    │
├─────────────────┬───────────────────────┤
│                 │                       │
│   File Upload   │    Chat Messages      │
│   Section       │    Display Area       │
│                 │                       │
│   Status &      │    Input Section      │
│   History       │    (Text + Files)     │
│                 │                       │
└─────────────────┴───────────────────────┘
```

## Implementation Components

### 1. Data Ingestion Section (`data_ingestion_ui.py`)

**Features:**
- File upload widget supporting PDF, DOCX, TXT, MD
- Drag & drop interface for multiple files
- Upload progress indicators
- Success/error feedback messages
- File processing status display
- Knowledge base statistics (total documents, last updated)

**Functions to implement:**
```python
def render_data_ingestion_section():
    # File upload interface
    # Process uploaded files using existing data_ingestion.py
    # Display upload status and results
    # Show knowledge base statistics
```

### 2. Chat Interface Section (`chat_ui.py`)

**Features:**
- Clean chat message display with user/AI message bubbles
- Multi-modal input support (text + image + document upload)
- File attachment previews
- Chat history persistence across sessions
- Export chat functionality
- Clear chat option

**Functions to implement:**
```python
def render_chat_section():
    # Display chat messages with proper formatting
    # Handle multi-modal input (text, images, documents)
    # Integrate with existing echo.py agent
    # Manage chat state and history
```

### 3. Main Application (`app.py`)

**Structure:**
```python
import streamlit as st
from data_ingestion_ui import render_data_ingestion_section
from chat_ui import render_chat_section
from services import vector_store  # Existing services
import echo  # Existing echo agent

def main():
    # Page configuration
    # Sidebar navigation
    # Main content area with tabs/sections
    # Session state management
```

## Technical Implementation Details

### Session State Management
- `st.session_state.chat_history` - Store chat messages
- `st.session_state.processing_status` - Track file processing
- `st.session_state.agent_state` - Maintain agent conversation state

### File Handling Integration
- Use existing `ingest_file_to_vectordb()` from `data_ingestion.py`
- Support multi-modal input parsing from `multiModalInputService.py`
- Integrate with existing chat management from `chat_mgmt.py`

### Agent Integration
- Import and use existing `rag_agent` from `echo.py`
- Maintain conversation flow with proper state management
- Handle tool calling responses (retrieval, JIRA ticket creation)

### UI/UX Design Principles
- **Clean Layout**: Use Streamlit columns and containers for organization
- **Responsive Design**: Adaptable to different screen sizes
- **Visual Feedback**: Progress bars, success/error messages, loading spinners
- **Intuitive Navigation**: Clear section headers and logical flow

## File Structure
```
├── app.py                 # Main Streamlit application
├── ui/
│   ├── __init__.py
│   ├── data_ingestion_ui.py    # Data ingestion interface
│   ├── chat_ui.py              # Chat interface
│   └── utils.py                # UI utility functions
├── static/                     # CSS, images if needed
└── requirements_ui.txt         # Additional UI dependencies
```

## Dependencies to Add
```
streamlit>=1.28.0
streamlit-chat>=0.1.1  # For better chat UI (optional)
streamlit-draggable-list  # For file management (optional)
```

## Implementation Steps
1. Create main `app.py` with basic layout and navigation
2. Implement data ingestion UI with file upload functionality
3. Create chat interface with message display and input handling
4. Integrate existing backend services (data_ingestion.py, echo.py)
5. Add session state management and chat persistence
6. Implement multi-modal input support in UI
7. Add visual enhancements and error handling
8. Test complete workflow and user experience

## Key Integration Points
- **Data Ingestion**: Direct integration with `ingest_file_to_vectordb()`
- **Chat Agent**: Use existing `rag_agent.invoke()` from echo.py
- **Multi-modal Support**: Leverage `parse_multimodal_input()` and related functions
- **Chat Management**: Use `load_chat_summary()` and `save_chat_summary()`
- **Vector Store**: Display statistics from existing `services.vector_store`

## User Experience Flow
1. **Data Management**: Upload files → See processing status → View knowledge base stats
2. **Chat Interaction**: Enter query (text/files/images) → See agent processing → Receive response with tool actions
3. **Session Management**: Persistent chat history → Export options → Clear functionality

## Phase-Wise Implementation Plan

### Phase 1: Minimal Viable UI (Essential Features Only)
**Duration**: 1-2 days  
**Goal**: Get basic functional UI working with core features

#### Backend Modifications Required:
- Create `echo_ui.py` - Wrapper functions to make echo.py compatible with Streamlit
- Modify data ingestion to return status/progress feedback
- Add simple vector store statistics function

#### UI Components:
1. **app.py** - Basic Streamlit app with two tabs
2. **Simple file upload** - Single file upload with basic feedback
3. **Basic chat interface** - Text input/output only
4. **Session state** - Basic chat history storage

#### Features Implemented:
- ✅ File upload (PDF, DOCX, TXT, MD)
- ✅ Basic text chat with RAG agent
- ✅ Simple success/error messages
- ✅ Chat history within session

#### What's NOT included in Phase 1:
- ❌ Multi-modal input (images/documents in chat)
- ❌ Advanced UI styling
- ❌ Knowledge base statistics
- ❌ Export functionality
- ❌ Multiple file uploads
- ❌ Chat persistence across sessions

### Phase 2: Core Functionality Enhancement
**Duration**: 2-3 days  
**Goal**: Add essential multi-modal capabilities and improve UX

#### Backend Modifications:
- Integrate multi-modal parsing with Streamlit file uploaders
- Add knowledge base statistics functions
- Enhance error handling and feedback

#### UI Enhancements:
1. **Multi-modal chat input** - Support for image and document uploads
2. **Knowledge base stats** - Show document count, last updated
3. **Better file upload** - Multiple files, progress indicators
4. **Improved chat display** - Better message formatting

#### Features Added:
- ✅ Image upload in chat queries
- ✅ Document upload in chat queries  
- ✅ Knowledge base statistics display
- ✅ Multiple file upload for data ingestion
- ✅ Progress indicators and better feedback

### Phase 3: Advanced Features & Polish
**Duration**: 2-3 days  
**Goal**: Add convenience features and improve user experience

#### Backend Additions:
- Chat export functionality
- Advanced session management
- Performance optimizations

#### UI Polish:
1. **Chat persistence** - Save/load chat across sessions
2. **Export functionality** - Download chat history
3. **Advanced styling** - Clean, professional appearance
4. **Error handling** - Comprehensive error management

#### Features Added:
- ✅ Chat persistence across sessions
- ✅ Export chat to file
- ✅ Clear chat functionality
- ✅ Advanced error handling and user feedback
- ✅ Professional styling and layout

## Detailed Phase 1 Implementation

### Files to Create:
```
app.py                    # Main application
echo_ui.py               # Backend wrapper for UI integration
requirements_ui.txt      # UI dependencies
```

### Phase 1 Backend Requirements:

#### echo_ui.py functions needed:
```python
def initialize_agent():
    # Initialize the rag_agent for UI use
    # Return agent instance
    
def process_user_message(message: str) -> str:
    # Process single text message through agent
    # Return AI response as string
    
def get_vector_store_status() -> dict:
    # Return basic stats about vector store
    # {"status": "ready/empty", "approx_docs": int}
```

#### data_ingestion.py modifications:
```python
def ingest_file_with_feedback(file_path: str) -> dict:
    # Modified version that returns detailed status
    # {"success": bool, "message": str, "file_name": str}
```

### Phase 1 Core Implementation Steps:
1. **Day 1 Morning**: Create app.py with basic layout and navigation
2. **Day 1 Afternoon**: Implement simple file upload with data_ingestion integration
3. **Day 2 Morning**: Create basic chat interface with echo_ui wrapper
4. **Day 2 Afternoon**: Add session state management and basic error handling

### Success Criteria for Phase 1:
- User can upload a single file and see success/failure message
- User can chat with text and get RAG responses
- Chat history persists within the session
- No crashes or major errors during basic operations

### Phase 2 & 3 Building Blocks:
Each phase builds incrementally on the previous, ensuring a working application at each stage while gradually adding complexity and features.