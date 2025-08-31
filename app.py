import streamlit as st
import os
import json
from pathlib import Path
import tempfile
from datetime import datetime
from echo_ui import (initialize_agent, process_user_message, get_vector_store_status, 
                     clear_chat_session, end_chat_session, export_chat_history)
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
        st.session_state.chat_history = load_persistent_chat()
    if 'processing_status' not in st.session_state:
        st.session_state.processing_status = []
    if 'agent_initialized' not in st.session_state:
        st.session_state.agent_initialized = False
    if 'input_key' not in st.session_state:
        st.session_state.input_key = 0

def save_persistent_chat():
    """Save chat history to persistent storage"""
    try:
        chat_file = Path("persistent_chat.json")
        with open(chat_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "chat_history": st.session_state.chat_history
            }, f, indent=2)
    except Exception as e:
        st.error(f"Failed to save chat: {str(e)}")

def load_persistent_chat():
    """Load chat history from persistent storage"""
    try:
        chat_file = Path("persistent_chat.json")
        if chat_file.exists():
            with open(chat_file, 'r') as f:
                data = json.load(f)
                return data.get("chat_history", [])
    except Exception as e:
        print(f"Failed to load persistent chat: {str(e)}")
    return []

def render_data_ingestion_section():
    """Render the data ingestion interface"""
    st.write("Upload files to add them to the knowledge base")
    
    # Multiple file upload widget
    uploaded_files = st.file_uploader(
        type=['pdf', 'docx', 'txt', 'md'],
        accept_multiple_files=True,
        help="Supported formats: PDF, DOCX, TXT, MD. You can select multiple files."
    )
    
    if uploaded_files:
        st.info(f"📄 {len(uploaded_files)} file(s) selected")
        
        # Show selected files
        with st.expander("Selected Files", expanded=False):
            for file in uploaded_files:
                st.write(f"• {file.name} ({file.size} bytes)")
        
        if st.button("Process All Files", type="primary"):
            # Create progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            results_container = st.container()
            
            total_files = len(uploaded_files)
            successful_files = 0
            failed_files = 0
            
            for i, uploaded_file in enumerate(uploaded_files):
                # Update progress
                progress = (i / total_files)
                progress_bar.progress(progress)
                status_text.text(f"Processing {uploaded_file.name}...")
                
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name
                
                try:
                    # Process file with feedback
                    result = ingest_file_with_feedback(tmp_file_path)
                    
                    with results_container:
                        if result["success"]:
                            st.success(f"✅ {result['file_name']}: {result['message']}")
                            st.session_state.processing_status.append(f"Success: {result['file_name']}")
                            successful_files += 1
                        else:
                            st.error(f"❌ {result['file_name']}: {result['message']}")
                            st.session_state.processing_status.append(f"Failed: {result['file_name']} - {result['message']}")
                            failed_files += 1
                            
                finally:
                    # Clean up temporary file
                    try:
                        os.unlink(tmp_file_path)
                    except:
                        pass
            
            # Final progress update
            progress_bar.progress(1.0)
            status_text.text(f"✅ Processing complete! {successful_files} successful, {failed_files} failed")
    
    # Show vector store status
    st.subheader("📊 Knowledge Base Status")
    
    # Create columns for status display
    col1, col2 = st.columns(2)
    
    vector_status = get_vector_store_status()
    
    with col1:
        if vector_status["status"] == "ready":
            st.metric("Documents", vector_status['approx_docs'], help="Approximate number of document chunks")
            st.success("✅ Vector store ready")
        elif vector_status["status"] == "empty":
            st.metric("Documents", "0")
            st.warning("📭 Vector store empty")
        else:
            st.metric("Documents", "Error")
            st.error(f"❌ {vector_status.get('error', 'Unknown error')}")
    
    with col2:
        # Refresh button for status
        if st.button("🔄 Refresh Status"):
            st.rerun()
    
    # Show processing history
    if st.session_state.processing_status:
        st.subheader("📋 Processing History")
        
        # Show recent entries with better formatting
        recent_entries = st.session_state.processing_status[-10:]  # Show last 10 entries
        for i, status in enumerate(reversed(recent_entries)):
            if "Success:" in status:
                st.success(f"{len(recent_entries) - i}. {status}")
            else:
                st.error(f"{len(recent_entries) - i}. {status}")
        
        # Clear history button
        if st.button("Clear History"):
            st.session_state.processing_status.clear()
            st.rerun()

def render_chat_section():
    """Render the enhanced chat interface"""
    
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
    
    # Chat management buttons at the top
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("📤 Export Chat", help="Download chat history"):
            if st.session_state.chat_history:
                # Create export options
                export_format = st.selectbox("Export format:", ["JSON", "Text"], key="export_format")
                
                if export_format == "JSON":
                    export_data = export_chat_history(st.session_state.chat_history, "json")
                    st.download_button(
                        label="Download JSON",
                        data=export_data,
                        file_name=f"echopilot_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
                else:
                    export_data = export_chat_history(st.session_state.chat_history, "txt")
                    st.download_button(
                        label="Download Text",
                        data=export_data,
                        file_name=f"echopilot_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )
            else:
                st.info("No chat history to export")
    
    with col2:
        if st.button("🔄 New Chat", help="Start a new chat session"):
            st.session_state.chat_history.clear()
            clear_chat_session()
            save_persistent_chat()
            st.rerun()
    
    with col3:
        if st.button("🔚 End Session", help="End chat session and save summary", type="primary"):
            result = end_chat_session()
            if result["success"]:
                st.success(result["message"])
                st.session_state.chat_history.clear()
                save_persistent_chat()
                st.rerun()
            else:
                st.error(result["message"])
    
    # Display chat history with better formatting
    if st.session_state.chat_history:
        st.subheader(f"💬 Conversation ({len(st.session_state.chat_history)} messages)")
        
        # Create a scrollable chat container
        chat_container = st.container()
        with chat_container:
            for i, message in enumerate(st.session_state.chat_history):
                if message["role"] == "user":
                    with st.chat_message("user", avatar="👤"):
                        st.markdown(message["content"])
                        # Display attached files if any
                        if "attachments" in message:
                            for attachment in message["attachments"]:
                                if attachment["type"] == "image":
                                    st.image(attachment["data"], caption=f"📷 {attachment['name']}", width=300)
                                elif attachment["type"] == "document":
                                    st.info(f"📄 Document: {attachment['name']}")
                else:
                    with st.chat_message("assistant", avatar="🤖"):
                        st.markdown(message["content"])
    
    # Create form to handle input and reset
    with st.form(key=f"chat_form_{st.session_state.input_key}", clear_on_submit=True):
        # Main input area
        user_input = st.text_area(
            "Your question:",
            placeholder="What would you like to know? You can also attach images or documents below...",
            height=120,
            key=f"user_input_{st.session_state.input_key}"
        )
        
        # File upload section with better organization
        st.write("📎 **Attach Files (Optional):**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("🖼️ **Images**")
            uploaded_images = st.file_uploader(
                type=['png', 'jpg', 'jpeg', 'gif', 'webp'],
                accept_multiple_files=True,
                key=f"chat_images_{st.session_state.input_key}",
                help="Upload images to analyze with your question"
            )
        
        with col2:
            st.write("📄 **Documents**")
            uploaded_docs = st.file_uploader(
                type=['pdf', 'txt', 'md', 'docx'],
                accept_multiple_files=True,
                key=f"chat_docs_{st.session_state.input_key}",
                help="Upload documents to include in your question"
            )
        
        # Send button
        send_button = st.form_submit_button("🚀 Send Message", type="primary", use_container_width=True)
        
        if send_button:
            if user_input.strip():
                # Process and save uploaded files temporarily
                image_files = []
                doc_files = []
                attachments = []
                
                # Handle image uploads
                if uploaded_images:
                    for uploaded_image in uploaded_images:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_image.name).suffix) as tmp_file:
                            tmp_file.write(uploaded_image.getvalue())
                            image_files.append(tmp_file.name)
                            attachments.append({
                                "type": "image",
                                "name": uploaded_image.name,
                                "data": uploaded_image.getvalue()
                            })
                
                # Handle document uploads
                if uploaded_docs:
                    for uploaded_doc in uploaded_docs:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_doc.name).suffix) as tmp_file:
                            tmp_file.write(uploaded_doc.getvalue())
                            doc_files.append(tmp_file.name)
                            attachments.append({
                                "type": "document",
                                "name": uploaded_doc.name,
                                "data": None
                            })
                
                # Create user message with attachments info
                user_message = {
                    "role": "user",
                    "content": user_input,
                    "timestamp": datetime.now().isoformat()
                }
                
                if attachments:
                    user_message["attachments"] = attachments
                
                st.session_state.chat_history.append(user_message)
                
                # Get AI response
                with st.spinner("🤔 Analyzing and thinking..."):
                    try:
                        ai_response = process_user_message(user_input, image_files, doc_files)
                        
                        # Add AI response to history
                        ai_message = {
                            "role": "assistant",
                            "content": ai_response,
                            "timestamp": datetime.now().isoformat()
                        }
                        st.session_state.chat_history.append(ai_message)
                        
                    except Exception as e:
                        error_msg = f"Sorry, I encountered an error: {str(e)}"
                        ai_message = {
                            "role": "assistant",
                            "content": error_msg,
                            "timestamp": datetime.now().isoformat()
                        }
                        st.session_state.chat_history.append(ai_message)
                    
                    finally:
                        # Clean up temporary files
                        for file_path in image_files + doc_files:
                            try:
                                os.unlink(file_path)
                            except:
                                pass
                
                # Save to persistent storage
                save_persistent_chat()
                
                # Increment input key to reset form
                st.session_state.input_key += 1
                
                # Rerun to update the display
                st.rerun()
            else:
                st.warning("⚠️ Please enter a question before sending.")
    
    # Help section
    with st.expander("💡 Tips & Help"):
        st.markdown("""
        **How to use EchoPilot:**
        
        1. **Text Questions**: Simply type your question in the text area above
        2. **Images**: Upload images to get visual analysis and context-aware responses
        3. **Documents**: Upload PDF, Word, or text files to analyze their content
        4. **Multi-modal**: Combine text, images, and documents in one question
        
        **Features:**
        - 🔍 **RAG Search**: Searches your knowledge base for relevant information
        - 🎫 **JIRA Integration**: Can create tickets for issues and requests
        - 💾 **Persistent History**: Your conversations are saved automatically
        - 📤 **Export**: Download your chat history in JSON or text format
        
        **Session Management:**
        - **New Chat**: Clears current conversation (history is saved)
        - **End Session**: Summarizes and saves current conversation, then clears it
        """)
    

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