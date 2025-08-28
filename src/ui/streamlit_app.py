"""
Main Streamlit application for EchoPilot
Customer Success Copilot with role-based access
"""

import streamlit as st
import sys
import os
import time
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
            st.session_state.session_handler.set_user_role(selected_role)
            # Role transition detected - switching to role-specific chat history
            st.rerun()
        
        # Display role info
        if current_role:
            #st.success(f"Logged in as: **{current_role.value.title()}**")
            
            # Show accessible knowledge bases
            role_manager = st.session_state.session_handler.get_role_manager()
            accessible_kbs = role_manager.get_accessible_knowledge_bases()
            
            #st.info(f"Access to: {', '.join(accessible_kbs)} knowledge base(s)")
        
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
                if "intent_analysis" in message and message["intent_analysis"]:
                    analysis = message["intent_analysis"]
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        try:
                            intent_text = analysis.intent.value if hasattr(analysis, 'intent') else 'unknown'
                        except AttributeError:
                            intent_text = 'unknown'
                        st.caption(f"Intent: {intent_text}")
                    with col2:
                        try:
                            urgency_text = analysis.urgency.value if hasattr(analysis, 'urgency') else 'unknown'
                        except AttributeError:
                            urgency_text = 'unknown'
                        st.caption(f"Urgency: {urgency_text}")
                    with col3:
                        try:
                            sentiment_text = analysis.sentiment.value if hasattr(analysis, 'sentiment') else 'unknown'
                        except AttributeError:
                            sentiment_text = 'unknown'
                        st.caption(f"Sentiment: {sentiment_text}")
                
                # Show ticket information if available
                if message["role"] == "assistant" and "ticket_info" in message and message["ticket_info"]:
                    ticket = message["ticket_info"]
                    with st.expander(f"🎫 Ticket Information - {ticket['local_ticket_id']}", expanded=False):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Type:** {ticket['ticket_type'].replace('_', ' ').title()}")
                            st.write(f"**Urgency:** {ticket['urgency'].title()}")
                        with col2:
                            st.write(f"**Local ID:** {ticket['local_ticket_id']}")
                            if ticket.get('jira_issue_key'):
                                st.write(f"**Jira Key:** {ticket['jira_issue_key']}")
                            else:
                                st.write("**Jira Key:** Mock ticket (development mode)")
                
                # Show source information if available
                if message["role"] == "assistant" and message.get("source_count", 0) > 0:
                    with st.expander(f"📚 Knowledge Sources ({message['source_count']})", expanded=False):
                        sources = message.get("sources", [])
                        for i, source in enumerate(sources[:3], 1):  # Show top 3 sources
                            st.write(f"**Source {i}:** {source.get('knowledge_base', 'unknown')} - {source.get('source', 'unknown')}")
                            if source.get('content'):
                                preview = source['content'][:200] + "..." if len(source['content']) > 200 else source['content']
                                st.write(f"*Preview:* {preview}")
                            st.write(f"*Relevance Score:* {source.get('score', 0):.2f}")
                            st.divider()
    
    # Chat input
    user_input = st.chat_input("Type your message here...")
    
    if user_input:
        # Add user message to current role's history
        user_message = {"role": "user", "content": user_input}
        st.session_state.session_handler.add_message_for_current_role(user_message)
        
        # Get current user role and chat history for context
        #   current_role = st.session_state.session_handler.get_current_user_role().value
        chat_history = st.session_state.session_handler.get_current_role_chat_history()
        
        # Process query with intelligent ticket creation
        response_data = st.session_state.rag_engine.process_query_with_ticket_creation(
            query=user_input,
            user_role=current_role,
            chat_history=chat_history
        )
        
        # Build enhanced assistant response
        assistant_content = response_data['response']
        
        # Add knowledge base attribution
        if response_data.get('knowledge_bases_used'):
            assistant_content += f"\n\n*Based on {', '.join(response_data['knowledge_bases_used'])} knowledge base(s)*"
        
        # Add ticket information if ticket was created
        if response_data.get('ticket_created') and response_data.get('ticket_info'):
            ticket_info = response_data['ticket_info']
            # Note: ticket creation details are already included in the response content
            pass  # Ticket details already included in the enhanced response
        
        # Add validation information for invalid complaints (for transparency)
        if response_data.get('validation_info') and not response_data['validation_info'].get('is_valid'):
            validation = response_data['validation_info']
            if validation.get('confidence', 0) > 0.7:  # Only show for high-confidence validations
                assistant_content += f"\n\n*Note: This appears to be a question rather than a complaint (confidence: {validation['confidence']:.1%})*"
        
        # Create assistant message with comprehensive metadata
        assistant_message = {
            "role": "assistant", 
            "content": assistant_content,
            "intent_analysis": response_data.get('intent_analysis', {}),
            "ticket_info": response_data.get('ticket_info'),
            "validation_info": response_data.get('validation_info'),
            "sources": response_data.get('sources', []),
            "source_count": response_data.get('source_count', 0)
        }
        
        st.session_state.session_handler.add_message_for_current_role(assistant_message)
        
        # Show success notification for ticket creation
        if response_data.get('ticket_created'):
            ticket_info = response_data['ticket_info']
            ticket_type = ticket_info['ticket_type'].replace('_', ' ').title()
            st.success(f"✅ {ticket_type} ticket created: {ticket_info['local_ticket_id']}")
        
        # Rerun to display new messages
        st.rerun()


def render_file_upload_section():
    """Render file upload section for Associates"""
    st.subheader("📁 Upload file to Knowledge Base")
    
    # Initialize upload completion tracking in session state
    if 'upload_completed' not in st.session_state:
        st.session_state.upload_completed = False
    if 'uploader_key' not in st.session_state:
        st.session_state.uploader_key = 0
    if 'last_upload_results' not in st.session_state:
        st.session_state.last_upload_results = None
    
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
    
    # File uploader with dynamic key to allow clearing
    uploaded_files = st.file_uploader(
        "Choose files to upload",
        #type=['txt', 'md', 'json', 'csv', 'pdf', 'docx', 'doc', 'jpg', 'jpeg', 'png', 'bmp', 'tiff'],
        accept_multiple_files=True,
        help="Supported formats: PDF, Word docs, Images, TXT, MD, JSON, CSV",
        key=f"file_uploader_{st.session_state.uploader_key}"
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
                
                # Still reset context even on critical failure
                st.session_state.upload_completed = True
                st.session_state.uploader_key += 1
                st.info("🔄 Context has been reset. Please try uploading again.")
                time.sleep(1)
                st.rerun()
                return
            
            # Display results with clear separation
            st.subheader("📊 Upload Results")
            
            successful = 0
            failed = 0
            total_chunks = 0
            successful_files = []
            failed_files = []
            
            # Categorize results
            for result in results:
                if result.success:
                    successful += 1
                    total_chunks += result.chunks_created
                    successful_files.append(result)
                else:
                    failed += 1
                    failed_files.append(result)
            
            # Display successful uploads
            if successful_files:
                st.success(f"✅ **Successfully Uploaded ({successful} files):**")
                for result in successful_files:
                    st.write(f"• {result.filename}")
                    if result.processing_time_seconds > 0:
                        st.caption(f"  └─ Processed in {result.processing_time_seconds:.2f}s, {result.chunks_created} chunks created")
            
            # Display failed uploads
            if failed_files:
                st.error(f"❌ **Upload Failed ({failed} files):**")
                for result in failed_files:
                    st.write(f"• {result.filename}: {result.message}")
                st.warning("⚠️ Failed files have been removed from the context.")
            
            # Get knowledge base stats for verification
            kb_manager = st.session_state.rag_engine.knowledge_base
            kb_stats = kb_manager.get_collection_stats()
            
            # Summary with actual knowledge base confirmation
            if successful > 0:
                actual_kb_name = "Internal Knowledge Base" if kb_type == "internal" else "General Knowledge Base"
                st.success(f"🎉 Successfully uploaded {successful} file(s) creating {total_chunks} chunks to the {actual_kb_name}")
                
                # Show knowledge base verification
                with st.expander("📊 Knowledge Base Verification", expanded=False):
                    st.write(f"**Target Knowledge Base:** {actual_kb_name} (kb_type: {kb_type})")
                    st.write(f"**Internal KB Documents:** {kb_stats.get('internal_documents', 0)}")
                    st.write(f"**General KB Documents:** {kb_stats.get('general_documents', 0)}")
                    st.write(f"**Total Documents:** {kb_stats.get('total_documents', 0)}")
            
            # Consolidated status message for both success and failure
            if failed > 0 and successful > 0:
                st.info(f"📄 Upload completed: {successful} successful, {failed} failed. Context will be reset.")
            elif failed > 0:
                st.info(f"📄 Upload completed: All {failed} files failed. Context will be reset.")
            elif successful > 0:
                st.info(f"📄 Upload completed: All {successful} files successful. Context will be reset.")
            
            # Show final memory stats
            final_memory = upload_manager._get_memory_usage()
            st.caption(f"Final memory usage: {final_memory.get('memory_mb', 0):.1f}MB")
            
            # Clear the file uploader and refresh after any upload (success or failure)
            st.info("💡 Upload process completed!")
            if successful > 0:
                st.success("✨ Knowledge base has been updated with new content!")
            
            # Always mark upload as completed and increment uploader key to clear files
            # This ensures context reset regardless of success/failure
            st.session_state.upload_completed = True
            st.session_state.uploader_key += 1
            
            # Add a brief delay to show status messages before clearing
            time.sleep(1)
            
            # Clear the context and refresh UI
            st.rerun()


def main():
    """Main application function"""
    initialize_app()
    render_sidebar()
    render_main_content()


if __name__ == "__main__":
    main()