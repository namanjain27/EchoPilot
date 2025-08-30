# file that keeps track of the code changes made by Claude Code on each session
# format: add time and very small description to what are the code changes made for

## SentenceTransformer ChromaDB Integration Fix
- Created wrapper class `SentenceTransformerEmbeddings` to make SentenceTransformer compatible with ChromaDB
- Added required `embed_documents` and `embed_query` methods that ChromaDB expects
- Fixed the embedding model initialization to work with the smaller, faster SentenceTransformer model

## Chat History Token Optimization
- Fixed chat history token optimization by cleaning metadata before LLM calls
- Chat history now sends only content field, removing unnecessary response_metadata, usage_metadata, and additional_kwargs
- This reduces token usage significantly for context preservation

## Chat History Persistence
- Added chat history save/load functionality using JSON format in chat_history.txt file
- Chat history is now automatically loaded on app startup and saved on exit (quit/exit commands)
- Supports both HumanMessage and AIMessage types for complete conversation persistence
- Fixed AIMessage content extraction bug in should_continue function by accessing result.content instead of passing entire result object

## Data Ingestion Updates
- Modified `ingest_file_to_vectordb()` to accept multiple file paths (string or list)
- Added error handling to skip unsupported/missing files and continue processing others
- Updated main section to handle comma-separated file inputs for batch processing

## Multi-Modal Image Support Implementation
- Added direct image processing capabilities using existing Gemini-2.5-flash model
- Implemented `process_image_to_base64()` helper function supporting PNG, JPG, JPEG, GIF, WEBP formats
- Created `parse_multimodal_input()` to extract image references from user input using 'image:' or 'img:' syntax
- Enhanced `running_agent()` to handle multi-modal HumanMessage content arrays with text and base64-encoded images
- Updated system prompt to include image analysis capabilities and decision flow for visual content
- No library changes required - leverages existing ChatGoogleGenerativeAI multi-modal support

## Comprehensive Multi-File Support Extension
- Extended multi-modal capabilities to support documents: PDF, TXT, MD, DOCX alongside existing image support
- Added `process_document_to_text()` function leveraging existing data_ingestion processors for real-time text extraction
- Enhanced `parse_multimodal_input()` to handle both images and documents with extended syntax: pdf:, txt:, md:, doc:
- Updated `running_agent()` for hybrid message construction combining document text content with image base64 encoding
- Supports complex queries like "Compare report pdf:/quarterly.pdf with chart image:/sales.png and notes txt:/meeting.txt"
- Real-time document processing eliminates vector store delays while maintaining full context analysis capability