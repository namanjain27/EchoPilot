"""
Main Streamlit application for EchoPilot
Customer Success Copilot with role-based access
"""

import streamlit as st
import sys
import os
from typing import List, Tuple

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from auth import UserRole, SessionHandler
from ai import IntentClassifier, RAGEngine
from data import FileUploadManager, UploadConfig, KnowledgeBaseManager


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
    
    # Initialize file upload manager
    if 'file_upload_manager' not in st.session_state:
        # Get KB manager from RAG engine
        kb_manager = st.session_state.rag_engine.kb_manager
        upload_config = UploadConfig(
            max_file_size_mb=float(os.getenv('MAX_FILE_SIZE_MB', '10.0')),
            max_files_per_batch=int(os.getenv('MAX_FILES_PER_BATCH', '10'))
        )
        st.session_state.file_upload_manager = FileUploadManager(kb_manager, upload_config)


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
        
        # File upload section (Associates only)
        if current_role == UserRole.ASSOCIATE:
            render_file_upload_section()
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


def render_file_upload_section():
    """Render file upload section for Associates"""
    st.subheader("📁 File Upload")
    
    # Knowledge base selector
    kb_options = {
        "Internal Knowledge Base": "internal",
        "General Knowledge Base": "general"
    }
    
    selected_kb = st.selectbox(
        "Select Knowledge Base:",
        options=list(kb_options.keys()),
        help="Choose which knowledge base to add the files to"
    )
    
    kb_type = kb_options[selected_kb]
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Choose files to upload",
        type=['txt', 'md', 'json', 'csv', 'pdf', 'docx', 'doc', 'jpg', 'jpeg', 'png', 'bmp', 'tiff'],
        accept_multiple_files=True,
        help="Supported formats: TXT, MD, JSON, CSV, PDF, Word documents, Images (JPG, PNG, etc.)"
    )
    
    if uploaded_files:
        # Show file information
        st.write(f"📋 **{len(uploaded_files)} file(s) selected:**")
        
        total_size_mb = 0
        file_info = []
        
        for file in uploaded_files:
            file_size_mb = len(file.getvalue()) / (1024 * 1024)
            total_size_mb += file_size_mb
            file_info.append(f"• {file.name} ({file_size_mb:.2f} MB)")
        
        for info in file_info:
            st.caption(info)
        
        st.caption(f"Total size: {total_size_mb:.2f} MB")
        
        # Upload button
        if st.button("📤 Upload Files", type="primary"):
            with st.spinner("Processing files..."):
                # Prepare files for upload
                files_data = []
                for file in uploaded_files:
                    files_data.append((file.name, file.getvalue()))
                
                # Process upload
                upload_manager = st.session_state.file_upload_manager
                results = upload_manager.upload_files(files_data, kb_type)
                
                # Display results
                st.subheader("📊 Upload Results")
                
                successful = 0
                failed = 0
                total_chunks = 0
                
                for result in results:
                    if result.success:
                        successful += 1
                        total_chunks += result.chunks_created
                        st.success(f"✅ {result.filename}: {result.message}")
                        if result.processing_time_seconds > 0:
                            st.caption(f"   Processed in {result.processing_time_seconds:.2f}s")
                    else:
                        failed += 1
                        st.error(f"❌ {result.filename}: {result.message}")
                
                # Summary
                if successful > 0:
                    st.success(f"🎉 Successfully uploaded {successful} file(s) creating {total_chunks} chunks in the {selected_kb.lower()}")
                
                if failed > 0:
                    st.warning(f"⚠️ {failed} file(s) failed to upload")
                
                # Refresh the knowledge base stats
                if successful > 0:
                    st.info("💡 Knowledge base has been updated with new content!")
                    # Clear the uploader by rerunning
                    st.rerun()


def main():
    """Main application function"""
    initialize_app()
    render_sidebar()
    render_main_content()


if __name__ == "__main__":
    main()