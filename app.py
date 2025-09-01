import streamlit as st
import os
from pathlib import Path
import tempfile
from echo_ui import initialize_agent, process_user_message, get_vector_store_status, clear_chat_session
from data_ingestion import ingest_file_with_feedback

# Page configuration
st.set_page_config(
    page_title="EchoPilot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_session_state():
    """Initialize session state variables"""
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'processing_status' not in st.session_state:
        st.session_state.processing_status = []
    if 'agent_initialized' not in st.session_state:
        st.session_state.agent_initialized = False
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = []

def render_data_ingestion_section():
    """Render the data ingestion interface"""
    st.header("📁 Data Ingestion")
    st.write("Upload files to add them to the knowledge base")
    
    # File upload widget
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['pdf', 'docx', 'txt', 'md'],
        help="Supported formats: PDF, DOCX, TXT, MD"
    )
    
    if uploaded_file is not None:
        if st.button("Process File"):
            with st.spinner("Processing file..."):
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name
                
                try:
                    # Process file with feedback
                    result = ingest_file_with_feedback(tmp_file_path)
                    
                    if result["success"]:
                        st.success(f"✅ {result['message']}")
                        st.session_state.processing_status.append(f"Success: {result['file_name']}")
                    else:
                        st.error(f"❌ {result['message']}")
                        st.session_state.processing_status.append(f"Failed: {result['file_name']} - {result['message']}")
                        
                finally:
                    # Clean up temporary file
                    try:
                        os.unlink(tmp_file_path)
                    except:
                        pass
    
    # Show vector store status
    st.subheader("Knowledge Base Status")
    vector_status = get_vector_store_status()
    
    if vector_status["status"] == "ready":
        st.info(f"📊 Vector store is ready with approximately {vector_status['approx_docs']} documents")
    elif vector_status["status"] == "empty":
        st.warning("📭 Vector store is empty. Upload some files to get started!")
    else:
        st.error(f"❌ Vector store error: {vector_status.get('error', 'Unknown error')}")
    
    # Show processing history
    if st.session_state.processing_status:
        st.subheader("Processing History")
        for status in st.session_state.processing_status[-5:]:  # Show last 5 entries
            st.text(status)

def render_chat_section():
    """Render the chat interface"""
    st.header("💬 Chat Interface")
    
    # Initialize agent if not already done
    if not st.session_state.agent_initialized:
        try:
            initialize_agent()
            st.session_state.agent_initialized = True
        except ValueError as e:
            st.error(f"⚠️ Agent initialization failed: {str(e)}")
            st.info("💡 Please ensure GOOGLE_API_KEY is set in your .env file")
            return
        except Exception as e:
            st.error(f"❌ Unexpected error initializing agent: {str(e)}")
            return
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for i, message in enumerate(st.session_state.chat_history):
            if message["role"] == "user":
                st.chat_message("user").write(message["content"])
            else:
                st.chat_message("assistant").write(message["content"])
    
    # File upload widget for chat
    st.subheader("📎 Attach Files (Optional)")
    uploaded_chat_files = st.file_uploader(
        "Upload images or documents to include in your query",
        type=['png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf', 'docx', 'txt', 'md'],
        accept_multiple_files=True,
        help="Supported: Images (PNG, JPG, JPEG, GIF, WEBP) and Documents (PDF, DOCX, TXT, MD)",
        key="chat_file_uploader"
    )
    
    # Display uploaded files
    if uploaded_chat_files:
        st.write("📁 **Attached Files:**")
        for file in uploaded_chat_files:
            file_type = "🖼️" if file.type.startswith('image/') else "📄"
            st.write(f"{file_type} {file.name} ({file.size} bytes)")
    
    # Chat input
    user_input = st.chat_input("What would you like to know?")
    
    if user_input:
        # Process uploaded files if any
        processed_files = None
        if uploaded_chat_files:
            with st.spinner("Processing uploaded files..."):
                from multiModalInputService import process_uploaded_files
                processed_files = process_uploaded_files(uploaded_chat_files)
        
        # Create display message with file info
        display_message = user_input
        if uploaded_chat_files:
            file_info = f"\n\n📎 **Attached Files:** {', '.join([f.name for f in uploaded_chat_files])}"
            display_message += file_info
        
        # Add user message to history
        st.session_state.chat_history.append({"role": "user", "content": display_message})
        
        # Display user message immediately
        with chat_container:
            st.chat_message("user").write(display_message)
        
        # Get AI response
        with st.spinner("Thinking..."):
            try:
                ai_response = process_user_message(user_input, processed_files)
                
                # Add AI response to history
                st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
                
                # Display AI response
                with chat_container:
                    st.chat_message("assistant").write(ai_response)
                    
            except Exception as e:
                error_msg = f"Sorry, I encountered an error: {str(e)}"
                st.session_state.chat_history.append({"role": "assistant", "content": error_msg})
                with chat_container:
                    st.chat_message("assistant").write(error_msg)
        
        # Clear the file uploader after processing
        st.session_state["chat_file_uploader"] = []
        
        # Rerun to update the display
        st.rerun()
    
    # Clear chat button
    if st.button("Clear Chat"):
        st.session_state.chat_history.clear()
        clear_chat_session()
        st.rerun()

def main():
    """Main application function"""
    # Initialize session state
    initialize_session_state()
    
    # App header
    st.title("🤖 EchoPilot")
    st.subheader("Customer Success Copilot")
    
    # Create tabs for main sections
    tab1, tab2 = st.tabs(["💬 Chat", "📁 Data Ingestion"])
    
    with tab1:
        render_chat_section()
    
    with tab2:
        render_data_ingestion_section()
    
    # Sidebar with additional info
    with st.sidebar:
        st.header("ℹ️ About EchoPilot")
        st.write("An intelligent AI assistant that helps with customer success queries using your knowledge base.")
        
        st.subheader("✨ Features")
        st.write("• RAG-based question answering")
        st.write("• JIRA ticket creation")
        st.write("• Multi-format document processing")
        st.write("• Persistent chat history")
        
        # Environment check
        if os.getenv("GOOGLE_API_KEY"):
            st.success("✅ API Key configured")
        else:
            st.error("❌ API Key not found")
            st.info("Add GOOGLE_API_KEY to your .env file")

if __name__ == "__main__":
    main()