from dotenv import load_dotenv
import os
from pathlib import Path
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, ToolMessage, AIMessage
from operator import add as add_messages
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from jira_tool import JiraTool
import services
from chat_mgmt import save_chat_history, load_chat_history
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

@tool
def retriever_tool(query: str) -> str:
    """
    This tool searches and returns the information from the Stock Market Performance 2024 document.
    """

    docs = retriever.invoke(query)
    if not docs: return "I found no relevant information in the Stock Market Performance 2024 document."
    
    results = []
    for i, doc in enumerate(docs):
        results.append(f"Document {i+1}:\\n{doc.page_content}")
    
    return "\\n\\n".join(results)


@tool
def create_jira_ticket(summary: str, description: str, labels: str) -> str:
    """
    Creates a JIRA ticket for service requests, complaints, and feature requests.
    
    Args: 
        summary: this would be the subject of the ticket. Keep it short and self-defining
        desc: description should contain all the necessary details to help the associates resolve the issue
        labels: Comma-separated labels with no spaces. Always have at least 2 values being - mode (associate or customer) and type (service request, complaints or feature request). (e.g., "customer,complaint" or "associate, feature_request")
    
    Returns:
        The created ticket key or error message
    """
    try:
        jira_tool = JiraTool()
        labels_list = [label.strip() for label in labels.split(",") if label.strip()]
        ticket_key = jira_tool.create_ticket(summary, description, labels_list)
        return f"Successfully created JIRA ticket: {ticket_key}"
    except Exception as e:
        return f"Failed to create JIRA ticket: {str(e)}"


tools = [retriever_tool, create_jira_ticket]


llm = init_chat_model("gemini-2.5-flash", model_provider="google_genai").bind_tools(tools)


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


def should_continue(state: AgentState):
    """Check if the last message contains tool calls."""
    result = state['messages'][-1]
    if (hasattr(result, 'tool_calls') and len(result.tool_calls) > 0):
        return True
    else:
        chat_history.append(AIMessage(content=result.content)) # saving only the final AI response
        return False


system_prompt = """
You are an intelligent AI assistant who answers questions based on the documents in your knowledge base, analyze images and perform tool calling. 
Use the retriever tool to get trusted answers, and you can make multiple calls if needed. Answer only the latest user query (earlier chats are context).
Always ask permission before ticket creation.
When images are provided:
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


tools_dict = {our_tool.name: our_tool for our_tool in tools} # Creating a dictionary of our tools

# LLM Agent
def call_llm(state: AgentState) -> AgentState:
    """Function to call the LLM with the current state."""
    messages = [SystemMessage(content=system_prompt)] + list(state['messages'])
    message = llm.invoke(messages)
    return {'messages': [message]}


# Tools Agent - retriever and ticket creation
def take_action(state: AgentState) -> AgentState:
    """Execute tool calls from the LLM's response."""

    tool_calls = state['messages'][-1].tool_calls
    results = []
    for t in tool_calls:
        print(f"Calling Tool: {t['name']} with query: {t['args'].get('query', 'No query provided')}")
        
        if not t['name'] in tools_dict: # Checks if a valid tool is present
            print(f"\\nTool: {t['name']} does not exist.")
            result = "Incorrect Tool Name, Please Retry and Select tool from List of Available tools."
        
        else:
            result = tools_dict[t['name']].invoke(t['args'])
            print(f"Result length: {len(str(result))}")
            

        # Appends the Tool Message
        results.append(ToolMessage(tool_call_id=t['id'], name=t['name'], content=str(result)))

    print("Tools Execution Complete. Back to the model!")
    return {'messages': results}


# Load chat history on startup
chat_history = load_chat_history()

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

rag_agent = graph.compile()


def running_agent():
    print("\n=== RAG AGENT===")
    print("Tip: Include files in your query using:")
    print("  Images: 'image:/path/to/chart.png' or 'img:/path/to/screenshot.jpg'")
    print("  Documents: 'pdf:/path/to/report.pdf', 'txt:/path/to/notes.txt', 'md:/path/to/readme.md', 'doc:/path/to/file.docx'")
    
    while True:
        user_input = input("\nWhat is your question: ")
        if user_input.lower() in ['exit', 'quit']:
            save_chat_history(chat_history)
            break
        
        # Parse input for multi-modal content
        clean_text, image_paths, doc_paths = parse_multimodal_input(user_input)
        
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
            # Text-only message (backward compatibility)
            human_message = HumanMessage(content=user_input)
        
        chat_history.append(human_message)
        result = rag_agent.invoke({"messages": chat_history})
        
        print("\n=== ANSWER ===")
        print(result['messages'][-1].content)


running_agent()