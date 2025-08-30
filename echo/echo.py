from dotenv import load_dotenv
import os
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, ToolMessage
from operator import add as add_messages
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from jira_tool import JiraTool
import data_ingestion

load_dotenv()

import getpass
import os

if not os.environ.get("GOOGLE_API_KEY"):
  os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter API key for Google Gemini: ")

# Now we create our retriever 
retriever = data_ingestion.vectorstore.as_retriever(
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
        chat_history.append(result) # saving only the final AI response
        return False


system_prompt = """
You are an intelligent AI assistant who answers questions about Stock Market Performance in 2024 based on the PDF document loaded into your knowledge base.
Use the retriever tool available to answer questions about the stock market performance data. You can make multiple calls if needed.
If you need to look up some information before asking a follow up question, you are allowed to do that!
Please always cite the specific parts of the documents you use in your answers.
"""


tools_dict = {our_tool.name: our_tool for our_tool in tools} # Creating a dictionary of our tools

# LLM Agent
def call_llm(state: AgentState) -> AgentState:
    """Function to call the LLM with the current state."""
    messages = list(state['messages'])
    messages = [SystemMessage(content=system_prompt)] + messages
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

# if chat file exists then take it else empty
chat_history = []

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
    print("\\n=== RAG AGENT===")
    
    while True:
        print(chat_history)
        print('\n\n')
        user_input = input("\nWhat is your question: ")
        if user_input.lower() in ['exit', 'quit']:
            # save the chat_history 
            break
            
        messages = [HumanMessage(content=user_input)] # converts back to a HumanMessage type
        chat_history.append[messages]
        result = rag_agent.invoke({"messages": chat_history})
        
        print("\n=== ANSWER ===")
        print(result['messages'][-1].content)


running_agent()