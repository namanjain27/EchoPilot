from dotenv import load_dotenv
import os
from pathlib import Path
from datetime import datetime
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, ToolMessage, AIMessage
from operator import add as add_messages
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from jira_tool import JiraTool
import services
from chat_mgmt import load_chat_summary, save_chat_summary
from multiModalInputService import process_image_to_base64, process_document_to_text, parse_multimodal_input

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
    
    # Create retriever
    retriever = services.vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5}
    )

    @tool
    def retriever_tool(query: str) -> str:
        """This tool searches and returns the information from the rentomojo knowledge base."""
        docs = retriever.invoke(query)
        if not docs: 
            return "I found no relevant information in my knowledge base."
        
        results = []
        for i, doc in enumerate(docs):
            results.append(f"Document {i+1}:\n{doc.page_content}")
        
        return "\n\n".join(results)

    @tool
    def create_jira_ticket(summary: str, description: str, labels: str) -> str:
        """Creates a JIRA ticket for service requests, complaints, and feature requests."""
        try:
            jira_tool = JiraTool()
            labels_list = [label.strip() for label in labels.split(",") if label.strip()]
            ticket_key = jira_tool.create_ticket(summary, description, labels_list)
            return f"Successfully created JIRA ticket: {ticket_key}"
        except Exception as e:
            return f"Failed to create JIRA ticket: {str(e)}"

    tools = [retriever_tool, create_jira_ticket]
    tools_dict = {our_tool.name: our_tool for our_tool in tools}

    base_llm = init_chat_model("gemini-2.5-flash", model_provider="google_genai")
    llm = base_llm.bind_tools(tools)

    class AgentState(TypedDict):
        messages: Annotated[Sequence[BaseMessage], add_messages]

    def should_continue(state: AgentState):
        """Check if the last message contains tool calls."""
        result = state['messages'][-1]
        if (hasattr(result, 'tool_calls') and len(result.tool_calls) > 0):
            return True
        else:
            _current_chat_messages.append(AIMessage(content=result.content))
            return False

    system_prompt_llm = """
You are an intelligent AI assistant who answers questions based on the documents in your knowledge base and perform tool calling. User query can contain images and extracted data from documents.  
Use the retriever tool to get trusted answers, and you can make multiple calls if needed. Answer only the latest user query (chat summary are for old context).
Always ask permission before ticket creation.
When images/added documents are provided:
- Analyze them thoroughly and describe relevant details
- Connect image content to knowledge base information when applicable
- Use image analysis to better understand customer issues or requests

Decision flow:
1. First check intent (query, complaint, service/feature request), as well as urgency and sentiment (these become ticket labels if a ticket is created).
2. If query → analyze any provided images, try a simple RAG answer with retriever. If not found, offer to create a ticket to add missing files into knowledge base.
3. If complaint →
3.1. If valid per KB or supported by image evidence → offer to create a complaint ticket.
3.2. If invalid per KB → explain reasons with citations.
3.3. If KB lacks enough info → still offer to create a ticket, and ask for any additional relevant details. 
4. If service/feature request → analyze images for context, ask any clarifying questions if needed, then offer to create a ticket.
"""

    def call_llm(state: AgentState) -> AgentState:
        """Function to call the LLM with the current state."""
        messages = [SystemMessage(content=system_prompt_llm)] + list(state['messages'])
        message = llm.invoke(messages)
        return {'messages': [message]}

    def take_action(state: AgentState) -> AgentState:
        """Execute tool calls from the LLM's response."""
        tool_calls = state['messages'][-1].tool_calls
        results = []
        for t in tool_calls:
            if not t['name'] in tools_dict:
                result = "Incorrect Tool Name, Please Retry and Select tool from List of Available tools."
            else:
                result = tools_dict[t['name']].invoke(t['args'])
            
            results.append(ToolMessage(tool_call_id=t['id'], name=t['name'], content=str(result)))

        return {'messages': results}

    # Build the graph
    graph = StateGraph(AgentState)
    graph.add_node("llm", call_llm)
    graph.add_node("tool_agent", take_action)
    graph.add_conditional_edges(
        "llm",
        should_continue,
        {True: "tool_agent", False: END}
    )
    graph.add_edge("tool_agent", "llm")
    graph.set_entry_point("llm")

    _rag_agent = graph.compile()
    
    # Load chat history
    _current_chat_messages.clear()
    _old_chat_summary = load_chat_summary()
    
    return _rag_agent

def process_user_message(message: str, image_files=None, doc_files=None) -> str:
    """Process multi-modal message through agent and return AI response as string"""
    global _current_chat_messages, _old_chat_summary
    
    if _rag_agent is None:
        initialize_agent()
    
    try:
        # Parse input for multi-modal content
        clean_text, image_paths, doc_paths = parse_multimodal_input(message)
        
        # Handle uploaded files from Streamlit
        if image_files:
            image_paths.extend(image_files)
        if doc_files:
            doc_paths.extend(doc_files)
        
        # Build comprehensive text content combining user query with document content
        full_text_content = clean_text
        
        # Process documents and add their content to the text
        if doc_paths:
            full_text_content += "\n\n--- Document Content ---\n"
            for doc_path in doc_paths:
                doc_text = process_document_to_text(doc_path)
                if doc_text:
                    file_name = Path(doc_path).name
                    full_text_content += f"\n[From {file_name}]:\n{doc_text}\n"
                else:
                    print(f"Skipping invalid document: {doc_path}")
        
        # Create message content
        if image_paths or doc_paths:
            # Multi-modal message with text and images
            message_content = [{"type": "text", "text": full_text_content}]
            
            # Add images as separate content items
            for image_path in image_paths:
                base64_image = process_image_to_base64(image_path)
                if base64_image:
                    # Determine image format for proper encoding
                    image_format = Path(image_path).suffix.lower().replace('.', '')
                    if image_format == 'jpg':
                        image_format = 'jpeg'
                    
                    message_content.append({
                        "type": "image_url",
                        "image_url": f"data:image/{image_format};base64,{base64_image}"
                    })
                else:
                    print(f"Skipping invalid image: {image_path}")
            
            human_message = HumanMessage(content=message_content)
        else:
            # Text-only message
            human_message = HumanMessage(content=full_text_content)
        
        _current_chat_messages.append(human_message)
        
        # Create messages list with summary context
        messages_with_context = []
        if _old_chat_summary.strip():
            messages_with_context.append(HumanMessage(content=f"Previous chat context: {_old_chat_summary}"))
        
        messages_with_context.extend(_current_chat_messages[:-1])
        messages_with_context.append(human_message)
        
        # Get response from agent
        result = _rag_agent.invoke({"messages": messages_with_context})
        
        # Return the AI response
        return result['messages'][-1].content
        
    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}"

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

def end_chat_session():
    """End current chat session gracefully with summary"""
    global _current_chat_messages, _old_chat_summary
    
    if not _current_chat_messages:
        return {"success": True, "message": "No active chat session to end"}
    
    try:
        # Import the summarization function from echo.py
        from echo import summarize_current_chat
        
        # Create summary of current chat
        updated_summary = summarize_current_chat(_current_chat_messages, _old_chat_summary)
        
        # Save the updated summary
        save_chat_summary(updated_summary)
        
        # Store message count for feedback
        message_count = len(_current_chat_messages)
        
        # Reset current chat and update summary
        _current_chat_messages.clear()
        _old_chat_summary = updated_summary
        
        return {
            "success": True, 
            "message": f"Chat session ended successfully. {message_count} messages summarized and saved."
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error ending chat session: {str(e)}"
        }

def save_current_chat_session():
    """Save current chat session to summary (legacy function)"""
    return end_chat_session()

def clear_chat_session():
    """Clear current chat session without saving"""
    global _current_chat_messages
    _current_chat_messages.clear()

def get_current_chat_messages():
    """Get current chat messages for display"""
    return _current_chat_messages.copy()

def export_chat_history(chat_history, format_type="json"):
    """Export chat history to downloadable format"""
    import json
    from datetime import datetime
    
    try:
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "total_messages": len(chat_history),
            "chat_history": []
        }
        
        for message in chat_history:
            export_message = {
                "role": message["role"],
                "content": message["content"],
                "timestamp": datetime.now().isoformat()  # We don't have original timestamps
            }
            
            # Include attachment info if present
            if "attachments" in message:
                export_message["attachments"] = [
                    {"type": att["type"], "name": att["name"]} 
                    for att in message["attachments"]
                ]
            
            export_data["chat_history"].append(export_message)
        
        if format_type == "json":
            return json.dumps(export_data, indent=2)
        elif format_type == "txt":
            # Plain text format
            text_export = f"EchoPilot Chat Export - {export_data['export_timestamp']}\n"
            text_export += f"Total Messages: {export_data['total_messages']}\n\n"
            text_export += "=" * 50 + "\n\n"
            
            for i, message in enumerate(export_data["chat_history"], 1):
                role = "User" if message["role"] == "user" else "Assistant"
                text_export += f"Message {i} - {role}:\n"
                text_export += f"{message['content']}\n"
                
                if "attachments" in message:
                    text_export += f"Attachments: {', '.join([att['name'] for att in message['attachments']])}\n"
                
                text_export += "\n" + "-" * 30 + "\n\n"
            
            return text_export
        
    except Exception as e:
        return f"Error exporting chat: {str(e)}"