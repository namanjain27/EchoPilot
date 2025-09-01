# UI for echopilot

## Current Status
1. chat implemented - (done)
2. single file dropbox for user query that takes both images and docs and internally sends to appropriate processor based on the file extension. Function already present in @multiModalInputService.py file
3. 'end chat' button that will initiate chat summarize and save it and clear the chat window.
4. 'clear chat' button is not needed
5. after sending the user query - the textbox and the files in context (if any) should be cleared. As their data has already come into the chat context.
6. file ingestion into knowledge base from Data ingestion tab (done)
7. after each file ingestion process -> clear the file context window as the file is already ingested and its ingestion status is visible. Just create a clear button for processing history.

## Implementation Plan

### Phase 1: Multi-modal File Upload in Chat Interface
**Target**: Add file upload capability to chat interface with visual feedback
- **Task 1.1**: Add file uploader widget in chat tab for images and documents
  - Support: PNG, JPG, JPEG, GIF, WEBP (images) and PDF, DOCX, TXT, MD (documents) 
  - Allow multiple files in single upload
  - Display uploaded files with preview/names before sending
- **Task 1.2**: Integrate with existing multiModalInputService.py functions
  - Use `process_uploaded_files()` to handle file processing
  - Process images to base64 for multimodal LLM input
  - Extract text from documents and append to query context
- **Task 1.3**: Update message processing pipeline
  - Modify `process_user_message()` in echo_ui.py to handle files
  - Combine text query + image data + document text for LLM processing
  - Clear file upload context after message is sent

### Phase 2: Enhanced Chat Session Management
**Target**: Replace "Clear Chat" with "End Chat" functionality
- **Task 2.1**: Replace "Clear Chat" button with "End Chat" button
  - Change button text and functionality
  - Trigger chat summarization before clearing
- **Task 2.2**: Implement chat session ending workflow
  - Call `save_current_chat_session()` from echo_ui.py
  - Show confirmation/success message to user
  - Clear chat history and reset session state

### Phase 3: UI/UX Improvements 
**Target**: Better user experience and cleanup workflows
- **Task 3.1**: Auto-clear input fields after message submission
  - Clear text input box after sending message
  - Clear file upload context after files are processed
- **Task 3.2**: Add "Clear Processing History" button in Data Ingestion tab
  - Clear `st.session_state.processing_status` list
  - Provide user control over processing history display
- **Task 3.3**: Enhanced visual feedback
  - Show file attachments in chat messages
  - Display processing status for multi-modal inputs
  - Add loading indicators for file processing

### Technical Considerations:
- Existing `multiModalInputService.py` has all required functions
- Need to update session state management for file contexts
- Must handle temporary file cleanup properly
- Ensure error handling for unsupported file types
- Maintain current RAG and tool calling functionality

