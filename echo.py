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

load_dotenv()

import getpass
import os


if not os.environ.get("GOOGLE_API_KEY"):
  os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter API key for Google Gemini: ")

# Now we create our retriever 
retriever = services.vector_store.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 5} # K is the amount of chunks to return
)

def get_tools():
    """Get the standard tools for the agent"""
    # Create retriever  
    retriever = services.vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5} # K is the amount of chunks to return
    )
    
    @tool
    def retriever_tool(query: str) -> str:
        """
        This tool searches and returns the information from the rentomojo knowledge base.
        """

        docs = retriever.invoke(query)
        if not docs: return "I found no relevant information in my knowledge base."
        
        results = []
        for i, doc in enumerate(docs):
            results.append(f"Document {i+1}:\\n{doc.page_content}")
        
        return "\\n\\n".join(results)

    @tool
    def create_jira_ticket(summary: str, description: str, intent: str, urgency: str, sentiment: str) -> str:
        """ Creates a jira ticket for service request, complaints and feature request.
            Args: 
                summary: this would be the subject of the ticket. Keep it short and self-defining
                description: description should contain all the necessary details to help the associates resolve the issue
                intent (one of): service_request, complaints or feature_request
                urgency (one of): high (if told critical or urgent), medium (default for complaint and service_request), low (else)
                sentiment (one of): positive (on receiving good remark), neutral (default), negative (if user expresses bad experience)
            returns: ticket id as string if success. None if failed to create ticket.
        """
        try:
            jira_tool = JiraTool()
            ticket_key = jira_tool.create_ticket(summary, description, intent, urgency, sentiment)
            return f"Successfully created JIRA ticket: {ticket_key}"
        except Exception as e:
            return f"Failed to create JIRA ticket: {str(e)}"

    return [retriever_tool, create_jira_ticket]


def create_agent():
    """Create and return a compiled RAG agent"""
    tools = get_tools()
    tools_dict = {our_tool.name: our_tool for our_tool in tools} # Creating a dictionary of our tools

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
            current_chat_messages.append(AIMessage(content=result.content)) # saving only the final AI response
            return False

    system_prompt_llm = """
You are an intelligent AI assistant who answers questions based on the documents in your knowledge base and perform tool calling. User query can contain images and extracted data from documents.  
Use the retriever tool to get trusted answers, and you can make multiple calls if needed. Answer only the latest user query (chat summary are for old context).
Always ask permission before ticket creation. You must only answer questions related to - Rentomojo and its services. This includes answering FAQs, queries related to service and TnC, analyzing service requests and complaints regarding renting furniture, functioning of Rentomojo's website and app. You should politely refuse questions outside of aforementioned domains, related to - joke, general world, news, general chit-chat.
When images/added documents are provided:
- Analyze them thoroughly and describe relevant details
- Connect image content to knowledge base information when applicable

Decision flow:
1. First check intent (query, complaint, service/feature request), as well as urgency and sentiment (will be used in creating jira ticket if needed).
2. If query → analyze any provided images, try a simple RAG answer with retriever. If not found, offer to create a ticket to add missing files into knowledge base.
3. If complaint →
3.1. If valid per KB or supported by image evidence → offer to create a complaint ticket.
3.2. If invalid per KB → explain reasons with citations.
4. If service/feature request → analyze images for context, ask any clarifying questions if needed, then offer to create a ticket.
"""

    # LLM Agent
    def call_llm(state: AgentState) -> AgentState:
        """Function to call the LLM with the current state."""
        messages = [SystemMessage(content=system_prompt_llm)] + list(state['messages'])
        message = llm.invoke(messages)
        return {'messages': [message]}

    # Tools Agent - retriever and ticket creation
    def take_action(state: AgentState) -> AgentState:
        """Execute tool calls from the LLM's response."""

        tool_calls = state['messages'][-1].tool_calls
        results = []
        for t in tool_calls:
            print(f"Calling Tool: {t['name']} with args: {t['args']}")
            
            if not t['name'] in tools_dict: # Checks if a valid tool is present
                print(f"\\nTool: {t['name']} does not exist.")
                result = "Incorrect Tool Name, Please Retry and Select tool from List of Available tools."
            
            else:
                try:
                    result = tools_dict[t['name']].invoke(t['args'])
                    print(f"Tool execution successful. Result length: {len(str(result))}")
                except Exception as e:
                    print(f"Tool execution failed with error: {str(e)}")
                    result = f"Tool execution failed: {str(e)}"
                

            # Appends the Tool Message
            results.append(ToolMessage(tool_call_id=t['id'], name=t['name'], content=str(result)))

        print("Tools Execution Complete. Back to the model!")
        return {'messages': results}

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

    return graph.compile()

# For backward compatibility, keep these at module level for CLI usage
tools = get_tools()
base_llm = init_chat_model("gemini-2.5-flash", model_provider="google_genai")
llm = base_llm.bind_tools(tools)
tools_dict = {our_tool.name: our_tool for our_tool in tools} # Creating a dictionary of our tools

# Load chat history on startup
current_chat_messages = []
old_chat_summary = load_chat_summary()

def summarize_current_chat(current_chat_messages, old_chat_summary):
    """Summarize current chat session and append to old summary with timestamp"""
    if not current_chat_messages: return old_chat_summary
    
    system_prompt = """Summarize the chat conversation provided. Include minimal but essential information.
    1. Always keep format for complete chat: user query: {what was requested}, AI response: {resolution provided with any ticket id if generated}
    2. Grade the chat session in terms of query resolution: A (fully resolved), B (partially resolved), C (unresolved)
    Keep the summary concise but informative for future context."""
    
    chat_to_summarize = [SystemMessage(content=system_prompt)] + current_chat_messages
    current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        unbounded_llm = llm.bind_tools([])
        current_chat_summary = unbounded_llm.invoke(chat_to_summarize)
        
        # Handle empty responses from Gemini
        if not current_chat_summary or not current_chat_summary.content or not current_chat_summary.content.strip():
            print("Warning: Gemini produced an empty response during summarization. Using fallback summary.")
            fallback_summary = f"\\n\\n=== Chat Session ({current_timestamp}) ===\\nModel gave empty response. Full chat {current_chat_messages}"
            return old_chat_summary + fallback_summary
        
        session_summary = f"\\n\\n=== Chat Session ({current_timestamp}) ==={current_chat_summary.content}"
        return old_chat_summary + session_summary
        
    except Exception as e:
        print(f"Error during chat summarization: {str(e)}")
        fallback_summary = f"\\n\\n=== Chat Session ({current_timestamp}) ===\\nChat session occurred but summary failed due to error: {str(e)}"
        return old_chat_summary + fallback_summary

rag_agent = create_agent()


def running_agent():
    """CLI entry point for backend-only usage"""
    print("\\n=== RAG AGENT===")
    print("Tip: Include files in your query using:")
    print("  Images: 'image:/path/to/chart.png' or 'img:/path/to/screenshot.jpg'")
    print("  Documents: 'pdf:/path/to/report.pdf', 'txt:/path/to/notes.txt', 'md:/path/to/readme.md', 'doc:/path/to/file.docx'")
    
    while True:
        user_input = input("\\nWhat is your question: ")
        if user_input.lower() in ['exit', 'quit']:
            # summarize current chat and update summary
            updated_summary = summarize_current_chat(current_chat_messages, old_chat_summary)
            # save updated summary
            save_chat_summary(updated_summary)
            break
        
        # Parse input for multi-modal content
        clean_text, image_paths, doc_paths = parse_multimodal_input(user_input)
        
        # Build comprehensive text content combining user query with document content
        full_text_content = clean_text
        
        # Process documents and add their content to the text
        if doc_paths:
            full_text_content += "\\n\\n--- Document Content ---\\n"
            for doc_path in doc_paths:
                doc_text = process_document_to_text(doc_path)
                if doc_text:
                    file_name = Path(doc_path).name
                    full_text_content += f"\\n[From {file_name}]:\\n{doc_text}\\n"
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
            # Text-only message (backward compatibility)
            human_message = HumanMessage(content=user_input)
        
        # Add human message to current chat
        current_chat_messages.append(human_message)
        
        # Create messages list with summary context, current chat messages, and new message
        messages_with_context = []
        if old_chat_summary.strip():
            messages_with_context.append(HumanMessage(content=f"Previous chat context: {old_chat_summary}"))
        
        # Add current ongoing chat messages for context
        messages_with_context.extend(current_chat_messages[:-1])  # Exclude the just-added human message to avoid duplication
        messages_with_context.append(human_message)
        
        result = rag_agent.invoke({"messages": messages_with_context})
        
        print("\\n=== ANSWER ===")
        print(result['messages'][-1].content)


# Only run the CLI interface if this file is executed directly
if __name__ == "__main__":
    running_agent()