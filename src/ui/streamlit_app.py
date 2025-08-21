"""
Main Streamlit application for EchoPilot
Customer Success Copilot with role-based access
"""

import streamlit as st
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from auth import UserRole, SessionHandler
from ai import IntentClassifier, RAGEngine


def initialize_app():
    """Initialize the application"""
    st.set_page_config(
        page_title="EchoPilot - Customer Success Copilot",
        page_icon="🤖",
        layout="wide"
    )
    
    # Initialize session handler
    if 'session_handler' not in st.session_state:
        st.session_state.session_handler = SessionHandler()
    
    # Initialize AI components
    if 'intent_classifier' not in st.session_state:
        st.session_state.intent_classifier = IntentClassifier()
    
    if 'rag_engine' not in st.session_state:
        st.session_state.rag_engine = RAGEngine()


def render_sidebar():
    """Render the sidebar with role selection and settings"""
    with st.sidebar:
        st.title("🤖 EchoPilot")
        st.markdown("Customer Success Copilot")
        
        st.divider()
        
        # Role selection
        st.subheader("User Role")
        
        current_role = st.session_state.session_handler.get_user_role()
        
        role_options = {
            "Select Role": None,
            "Associate": UserRole.ASSOCIATE,
            "Customer": UserRole.CUSTOMER
        }
        
        # Get current role display name
        current_display = "Select Role"
        for display_name, role in role_options.items():
            if role == current_role:
                current_display = display_name
                break
        
        selected_role_display = st.selectbox(
            "Choose your role:",
            options=list(role_options.keys()),
            index=list(role_options.keys()).index(current_display)
        )
        
        selected_role = role_options[selected_role_display]
        
        # Update role if changed
        if selected_role != current_role:
            if selected_role:
                st.session_state.session_handler.set_user_role(selected_role)
                st.rerun()
        
        # Display role info
        if current_role:
            st.success(f"Logged in as: **{current_role.value.title()}**")
            
            # Show accessible knowledge bases
            role_manager = st.session_state.session_handler.get_role_manager()
            accessible_kbs = role_manager.get_accessible_knowledge_bases()
            
            st.info(f"Access to: {', '.join(accessible_kbs)} knowledge base(s)")
        
        st.divider()
        
        # Chat controls
        if st.button("Clear Chat History", type="secondary"):
            st.session_state.session_handler.clear_chat_history()
            st.rerun()
        
        # Show chat stats
        chat_history = st.session_state.session_handler.get_chat_history()
        st.caption(f"Messages in this session: {len(chat_history)}")


def render_main_content():
    """Render the main chat interface"""
    current_role = st.session_state.session_handler.get_user_role()
    
    if not current_role:
        st.warning("Please select your role from the sidebar to continue.")
        return
    
    # Main chat interface
    st.title(f"EchoPilot - {current_role.value.title()} Mode")
    
    # Display role-specific information
    if current_role == UserRole.ASSOCIATE:
        st.info("🔹 Associate Mode: You have access to internal knowledge base and can create feature request tickets.")
    else:
        st.info("🔸 Customer Mode: You can ask questions and submit complaints or service requests.")
    
    # Chat history display
    chat_history = st.session_state.session_handler.get_chat_history()
    
    # Create a container for chat messages
    chat_container = st.container()
    
    with chat_container:
        for message in chat_history:
            with st.chat_message(message["role"]):
                st.write(message["content"])
                
                # Show intent analysis if available
                if "intent_analysis" in message:
                    analysis = message["intent_analysis"]
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.caption(f"Intent: {analysis['intent']}")
                    with col2:
                        st.caption(f"Urgency: {analysis['urgency']}")
                    with col3:
                        st.caption(f"Sentiment: {analysis['sentiment']}")
    
    # Chat input
    user_input = st.chat_input("Type your message here...")
    
    if user_input:
        # Add user message to history
        user_message = {"role": "user", "content": user_input}
        st.session_state.session_handler.add_message(user_message)
        
        # Analyze intent
        intent_analysis = st.session_state.intent_classifier.analyze_message(user_input)
        
        # Get accessible knowledge bases
        role_manager = st.session_state.session_handler.get_role_manager()
        accessible_kbs = role_manager.get_accessible_knowledge_bases()
        
        # Get chat history for context
        chat_history = st.session_state.session_handler.get_chat_history()
        
        # Generate response using RAG with chat history
        rag_response = st.session_state.rag_engine.search_knowledge_base(
            user_input, accessible_kbs, chat_history
        )
        
        # Create assistant response
        assistant_content = f"{rag_response['response']}\n\n"
        assistant_content += f"*Based on {', '.join(rag_response['knowledge_bases_used'])} knowledge base(s)*"
        
        assistant_message = {
            "role": "assistant", 
            "content": assistant_content,
            "intent_analysis": {
                "intent": intent_analysis.intent.value,
                "urgency": intent_analysis.urgency.value,
                "sentiment": intent_analysis.sentiment.value
            }
        }
        
        st.session_state.session_handler.add_message(assistant_message)
        
        # Rerun to display new messages
        st.rerun()


def main():
    """Main application function"""
    initialize_app()
    render_sidebar()
    render_main_content()


if __name__ == "__main__":
    main()