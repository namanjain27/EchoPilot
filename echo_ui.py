from dotenv import load_dotenv
import os
from pathlib import Path
from datetime import datetime
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, ToolMessage, AIMessage
from operator import add as add_messages
from langchain.chat_models import init_chat_model
from chat_mgmt import load_chat_summary, save_chat_summary
from multiModalInputService import process_image_to_base64, process_document_to_text, parse_multimodal_input
# Import centralized agent creation from echo.py
from echo import create_agent, get_tools
import services

# Load environment variables
load_dotenv()

# Global variables for agent initialization
_rag_agent = None
_current_chat_messages = []
_old_chat_summary = ""

def initialize_agent():
    """Initialize the RAG agent for UI use"""
    global _rag_agent, _current_chat_messages, _old_chat_summary
    
    if _rag_agent is not None:
        return _rag_agent
    
    # Set up API key if not present
    if not os.environ.get("GOOGLE_API_KEY"):
        raise ValueError("GOOGLE_API_KEY environment variable not set")
    
    # Use centralized agent creation from echo.py
    _rag_agent = create_agent()
    
    # Load chat history
    _current_chat_messages.clear()
    _old_chat_summary = load_chat_summary()
    
    return _rag_agent

def process_user_message(message: str, processed_files=None) -> str:
    """Process text message with optional files through agent and return AI response as string"""
    global _current_chat_messages, _old_chat_summary
    
    if _rag_agent is None:
        initialize_agent()
    
    try:
        # Initialize message content
        message_content = message
        
        # Process uploaded files if provided
        if processed_files:
            from multiModalInputService import process_image_to_base64, process_document_to_text
            import os
            
            # Process images to base64
            image_data = []
            for image_path in processed_files.get("image_files", []):
                base64_data = process_image_to_base64(image_path)
                if base64_data:
                    image_data.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_data}"}
                    })
                # Clean up temp file
                try:
                    os.unlink(image_path)
                except:
                    pass
            
            # Process documents to text
            doc_text = ""
            for doc_path in processed_files.get("doc_files", []):
                text_content = process_document_to_text(doc_path)
                if text_content:
                    doc_text += f"\\n\\nDocument content:\\n{text_content}"
                # Clean up temp file
                try:
                    os.unlink(doc_path)
                except:
                    pass
            
            # Create multi-modal message content
            if image_data or doc_text:
                # Combine text with document content
                combined_text = message + doc_text
                
                if image_data:
                    # Multi-modal content with images
                    content = [{"type": "text", "text": combined_text}] + image_data
                    human_message = HumanMessage(content=content)
                else:
                    # Text only with document content
                    human_message = HumanMessage(content=combined_text)
            else:
                human_message = HumanMessage(content=message)
        else:
            # Text-only message
            human_message = HumanMessage(content=message)
        
        _current_chat_messages.append(human_message)
        
        # Create messages list with summary context
        messages_with_context = []
        if _old_chat_summary.strip():
            messages_with_context.append(HumanMessage(content=f"Previous chat context: {_old_chat_summary}"))
        
        messages_with_context.extend(_current_chat_messages[:-1])
        messages_with_context.append(human_message)
        
        # Get response from agent
        result = _rag_agent.invoke({"messages": messages_with_context})
        
        # Save AI response to current chat messages
        ai_response = AIMessage(content=result['messages'][-1].content)
        _current_chat_messages.append(ai_response)
        
        # Return the AI response
        return result['messages'][-1].content
        
    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}"

def _summarize_current_chat(current_chat_messages, old_chat_summary):
    """Summarize current chat session and append to old summary with timestamp"""
    if not current_chat_messages: 
        return old_chat_summary
    
    system_prompt = """Summarize the chat conversation provided. Include minimal but essential information.
    1. Always keep format for complete chat: user query: {what was requested}, AI response: {resolution provided with any ticket id if generated}
    2. Grade the chat session in terms of query resolution: A (fully resolved), B (partially resolved), C (unresolved)
    Keep the summary concise but informative for future context."""
    
    chat_to_summarize = [SystemMessage(content=system_prompt)] + current_chat_messages
    current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        # Use the same LLM instance but without tools for summarization
        base_llm = init_chat_model("gemini-2.5-flash", model_provider="google_genai")
        current_chat_summary = base_llm.invoke(chat_to_summarize)
        
        # Handle empty responses from Gemini
        if not current_chat_summary or not current_chat_summary.content or not current_chat_summary.content.strip():
            print("Warning: Gemini produced an empty response during summarization. Using fallback summary.")
            fallback_summary = f"\\n\\n=== Chat Session ({current_timestamp}) ===\\nModel gave empty response. Full chat {current_chat_messages}"
            return old_chat_summary + fallback_summary
        
        session_summary = f"\\n\\n=== Chat Session ({current_timestamp}) ===\\n{current_chat_summary.content}"
        return old_chat_summary + session_summary
        
    except Exception as e:
        print(f"Error during chat summarization: {str(e)}")
        fallback_summary = f"\\n\\n=== Chat Session ({current_timestamp}) ===\\nChat session occurred but summary failed due to error: {str(e)}"
        return old_chat_summary + fallback_summary

def get_vector_store_status() -> dict:
    """Return basic stats about vector store"""
    try:
        # Get collection info from ChromaDB
        collection = services.vector_store._collection
        count = collection.count()
        
        if count > 0:
            return {"status": "ready", "approx_docs": count}
        else:
            return {"status": "empty", "approx_docs": 0}
            
    except Exception as e:
        return {"status": "error", "approx_docs": 0, "error": str(e)}

def save_current_chat_session():
    """Save current chat session to summary"""
    global _current_chat_messages, _old_chat_summary
    
    if not _current_chat_messages:
        return
    
    try:
        # Use local summarization logic to avoid importing echo.py's main execution
        updated_summary = _summarize_current_chat(_current_chat_messages, _old_chat_summary)
        save_chat_summary(updated_summary)
        
        # Reset current chat
        _current_chat_messages.clear()
        _old_chat_summary = updated_summary
        
    except Exception as e:
        print(f"Error saving chat session: {str(e)}")

def clear_chat_session():
    """Clear current chat session"""
    global _current_chat_messages
    _current_chat_messages.clear()

def get_current_chat_messages():
    """Get current chat messages for display"""
    return _current_chat_messages.copy()