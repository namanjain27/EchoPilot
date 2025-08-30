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