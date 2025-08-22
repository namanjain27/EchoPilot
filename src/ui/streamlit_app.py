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
    
    # Add custom CSS to make selectboxes non-editable
    st.markdown("""
        <style>
        /* Disable text input in selectboxes */
        .stSelectbox > div > div > input[type="text"] {
            pointer-events: none !important;
            cursor: pointer !important;
            caret-color: transparent !important;
        }
        
        /* Ensure the selectbox container is clickable */
        .stSelectbox > div > div {
            cursor: pointer !important;
        }
        
        /* Hide the text cursor completely */
        .stSelectbox input {
            pointer-events: none !important;
            cursor: pointer !important;
            caret-color: transparent !important;
        }
        
        /* Style the dropdown arrow to be more prominent */
        .stSelectbox [data-baseweb="select"] {
            cursor: pointer !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
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
        kb_manager = st.session_state.rag_engine.knowledge_base
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
            index=list(role_options.keys()).index(current_display),
            disabled=False,
            key="role_selector"
        )
        
        selected_role = role_options[selected_role_display]
        
        # Update role if changed
        if selected_role != current_role:
            if selected_role:
                st.session_state.session_handler.set_user_role(selected_role)
                # Role transition detected - switching to role-specific chat history
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
            st.session_state.session_handler.clear_current_role_chat_history()
            st.rerun()
        
        # Show role-specific chat stats
        if current_role:
            current_role_history = st.session_state.session_handler.get_current_role_chat_history()
            st.caption(f"Messages in {current_role.value} mode: {len(current_role_history)}")
        else:
            st.caption("Select a role to see message count")


def render_welcome_page():
    """Render welcome page when no role is selected"""
    # Main title and header
    st.title("🤖 Welcome to EchoPilot")
    st.subheader("Your AI-Powered Customer Success Copilot")
    
    # Main description
    st.markdown("""
    EchoPilot is an intelligent customer success assistant designed to streamline support workflows 
    and enhance customer interactions through AI-powered knowledge retrieval and analysis.
    """)
    
    st.divider()
    
    # Features overview
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🎯 **Key Features**")
        st.markdown("""
        - 🧠 **Intelligent Knowledge Retrieval**: Access relevant information instantly
        - 🔍 **Intent Analysis**: Automatic classification of user queries
        - 📊 **Sentiment Analysis**: Understanding customer emotions
        - 🎫 **Ticket Management**: Streamlined issue tracking
        - 📁 **Document Processing**: Upload and process various file formats
        """)
    
    with col2:
        st.markdown("### 🚀 **How EchoPilot Helps**")
        st.markdown("""
        - ⚡ **Faster Response Times**: Get answers from knowledge base instantly
        - 📈 **Better Customer Experience**: Personalized and accurate responses
        - 🔒 **Role-Based Access**: Secure access to relevant information
        - 📋 **Context-Aware**: Maintains conversation history
        - 🎯 **Smart Routing**: Automatically categorizes and prioritizes requests
        """)
    
    st.divider()
    
    # Role selection guidance
    st.markdown("### 👥 **Choose Your Role to Get Started**")
    
    role_col1, role_col2 = st.columns(2)
    
    with role_col1:
        st.info("""
        **🔹 Associate Mode**
        
        *For internal team members*
        
        **Access to:**
        - Internal knowledge base
        - Feature request creation
        - Ticket management tools
        - Advanced analytics
        - File upload capabilities
        
        **Use Cases:**
        - Customer support inquiries
        - Internal documentation lookup
        - Feature request processing
        - Technical troubleshooting
        """)
    
    with role_col2:
        st.info("""
        **🔸 Customer Mode**
        
        *For external customers*
        
        **Access to:**
        - General knowledge base
        - Public documentation
        - Service requests
        - Complaint submission
        - Basic support features
        
        **Use Cases:**
        - General product questions
        - Service requests
        - Bug reports
        - Account-related inquiries
        """)
    
    st.divider()
    
    # Call to action
    st.markdown("### 📋 **Getting Started**")
    st.success("""
    **Ready to begin?** Please select your role from the sidebar to start using EchoPilot!
    
    👈 Use the **"Choose your role"** dropdown in the sidebar to get started.
    """)
    
    # Additional information
    st.markdown("### ℹ️ **Additional Information**")
    with st.expander("📘 Learn More About EchoPilot"):
        st.markdown("""
        **Technology Stack:**
        - 🤖 Advanced AI/ML models for natural language processing
        - 🔍 Vector-based knowledge retrieval (RAG)
        - 📊 Real-time sentiment and intent analysis
        - 🗃️ Integrated knowledge base management
        
        **Security & Privacy:**
        - Role-based access control
        - Secure knowledge base isolation
        - Conversation history protection
        - Enterprise-grade security features
        
        **Supported File Types:**
        - Documents: PDF, Word (DOC/DOCX)
        - Text: TXT, Markdown (MD)
        - Data: JSON, CSV
        - Images: JPG, PNG, BMP, TIFF
        """)


def render_main_content():
    """Render the main chat interface or welcome page"""
    current_role = st.session_state.session_handler.get_user_role()
    
    if not current_role:
        # Show welcome page when no role is selected
        render_welcome_page()
        return
    
    # Main chat interface
    st.title(f"EchoPilot - {current_role.value.title()} Mode")
    
    # Display role-specific information
    if current_role == UserRole.ASSOCIATE:
        st.info("🔹 Associate Mode: You have access to internal knowledge base and can create feature request tickets.")
    else:
        st.info("🔸 Customer Mode: You can ask questions and submit complaints or service requests.")
    
    # Chat history display - get current role's chat history
    chat_history = st.session_state.session_handler.get_current_role_chat_history()
    
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
        # Add user message to current role's history
        user_message = {"role": "user", "content": user_input}
        st.session_state.session_handler.add_message_for_current_role(user_message)
        
        # Analyze intent
        intent_analysis = st.session_state.intent_classifier.analyze_message(user_input)
        
        # Get accessible knowledge bases
        role_manager = st.session_state.session_handler.get_role_manager()
        accessible_kbs = role_manager.get_accessible_knowledge_bases()
        
        # Get current role's chat history for context
        chat_history = st.session_state.session_handler.get_current_role_chat_history()
        
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
        
        st.session_state.session_handler.add_message_for_current_role(assistant_message)
        
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
        help="Choose which knowledge base to add the files to",
        key="kb_selector"
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
            # Create progress indicators
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.text("🔄 Preparing files for upload...")
                
                # Prepare files for upload
                files_data = []
                for i, file in enumerate(uploaded_files):
                    files_data.append((file.name, file.getvalue()))
                    progress_bar.progress((i + 1) / len(uploaded_files) * 0.2)  # 20% for preparation
                
                status_text.text("🔄 Processing files through knowledge base...")
                
                # Process upload with timeout protection
                upload_manager = st.session_state.file_upload_manager
                
                # Show memory stats before processing
                memory_stats = upload_manager._get_memory_usage()
                status_text.text(f"🔄 Processing files... (Memory: {memory_stats.get('memory_mb', 0):.1f}MB)")
                
                results = upload_manager.upload_files(files_data, kb_type)
                
                # Complete progress
                progress_bar.progress(1.0)
                status_text.text("✅ Processing complete!")
                
            except Exception as e:
                progress_bar.progress(1.0)
                status_text.text(f"❌ Upload failed: {str(e)}")
                st.error(f"Upload error: {e}")
                return
            
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
            
            # Show final memory stats
            final_memory = upload_manager._get_memory_usage()
            st.caption(f"Final memory usage: {final_memory.get('memory_mb', 0):.1f}MB")
            
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