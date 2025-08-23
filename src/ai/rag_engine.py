"""
RAG (Retrieval Augmented Generation) engine for EchoPilot
Handles knowledge retrieval and response generation using Gemini
"""

from typing import List, Dict, Any
import logging
from .gemini_client import GeminiClient
from .tool_framework import ToolFramework, ToolCall
from .complaint_validator import ComplaintValidator
from .intent_classifier import IntentClassifier
from src.data.knowledge_base import KnowledgeBaseManager
from src.integrations.ticket_manager import TicketManager
from src.integrations.jira_client import JiraClient

# Configure logging
logger = logging.getLogger(__name__)


class RAGEngine:
    """Retrieval Augmented Generation engine for knowledge-based responses"""
    
    def __init__(self):
        """Initialize RAG engine with Gemini client and knowledge base"""
        # Initialize Gemini client for response generation
        self.gemini_client = GeminiClient()
        
        # Initialize knowledge base manager
        try:
            self.knowledge_base = KnowledgeBaseManager()
            logger.info("Knowledge base manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize knowledge base: {e}")
            self.knowledge_base = None
        
        # Initialize supporting components
        self.intent_classifier = IntentClassifier()
        self.ticket_manager = TicketManager()
        self.jira_client = JiraClient()
        
        # Initialize advanced components
        self.complaint_validator = ComplaintValidator(self, self.gemini_client)
        self.tool_framework = ToolFramework(self, self.ticket_manager, self.jira_client)
        
        logger.info("RAG Engine initialized with ticket creation capabilities")
    
    def retrieve_documents(self, query: str, user_role: str, top_k: int = 5, limit: int = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents from knowledge bases based on user role
        
        Args:
            query: User query
            user_role: User role (associate/customer)
            top_k: Number of documents to retrieve
            
        Returns:
            List of relevant documents with metadata
        """
        if not self.knowledge_base:
            logger.warning("Knowledge base not available, using fallback")
            return self._fallback_retrieve(query, user_role, top_k)
        
        try:
            # Search all accessible knowledge bases for the user role
            all_results = self.knowledge_base.search_all_accessible(
                query=query,
                user_role=user_role,
                n_results=top_k
            )
            
            # Convert to unified format
            documents = []
            for kb_name, results in all_results.items():
                for i, (doc, metadata, distance, doc_id) in enumerate(zip(
                    results['documents'],
                    results['metadatas'], 
                    results['distances'],
                    results['ids']
                )):
                    documents.append({
                        "content": doc,
                        "source": doc_id,
                        "score": 1 - distance,  # Convert distance to similarity score
                        "knowledge_base": kb_name,
                        "metadata": metadata
                    })
            
            # Sort by score and return top_k (use limit if specified)
            documents.sort(key=lambda x: x['score'], reverse=True)
            return_count = limit if limit is not None else top_k
            return documents[:return_count]
            
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return self._fallback_retrieve(query, user_role, top_k)
    
    def generate_response(self, query: str, context_docs: List[Dict[str, Any]], chat_history: List[Dict[str, Any]], knowledge_bases: List[str]) -> str:
        """
        Generate response using retrieved context and chat history with Gemini
        
        Args:
            query: User query
            context_docs: Retrieved context documents
            chat_history: Previous conversation history
            knowledge_bases: List of knowledge bases used
            
        Returns:
            Generated response string
        """
        try:
            # Use Gemini client to generate RAG response
            response = self.gemini_client.generate_rag_response(
                user_query=query,
                context_documents=context_docs,
                knowledge_bases=knowledge_bases,
                chat_history=chat_history
            )
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            # Fallback to simple response
            context_summary = self._summarize_context(context_docs)
            return f"Based on the available information from {', '.join(knowledge_bases)} knowledge base(s): {context_summary}. I hope this helps with your query about: {query}"
    
    def _summarize_context(self, context_docs: List[Dict[str, Any]]) -> str:
        """Summarize context documents for response generation"""
        if not context_docs:
            return "No specific context found"
        
        # Simple concatenation for prototype
        return " ".join([doc.get("content", "")[:200] for doc in context_docs])
    
    def _fallback_retrieve(self, query: str, user_role: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Fallback document retrieval when knowledge base is unavailable"""
        mock_documents = []
        
        # Determine accessible knowledge bases based on role
        accessible_kbs = ['general']
        if user_role.lower() == 'associate':
            accessible_kbs.append('internal')
        
        # Generate knowledge base specific mock documents
        for kb in accessible_kbs:
            if kb == "general":
                mock_documents.extend([
                    {
                        "content": f"General information related to: {query}. Our platform provides comprehensive solutions for customer success management.",
                        "source": "general_kb_fallback",
                        "score": 0.85,
                        "knowledge_base": "general",
                        "metadata": {"category": "general", "type": "fallback"}
                    },
                    {
                        "content": "Frequently asked questions and troubleshooting guides are available in our documentation section.",
                        "source": "general_faq_fallback",
                        "score": 0.75,
                        "knowledge_base": "general",
                        "metadata": {"category": "support", "type": "fallback"}
                    }
                ])
            elif kb == "internal":
                mock_documents.extend([
                    {
                        "content": f"Internal documentation for: {query}. This includes detailed technical specifications and internal procedures.",
                        "source": "internal_docs_fallback",
                        "score": 0.90,
                        "knowledge_base": "internal",
                        "metadata": {"category": "internal", "type": "fallback", "confidentiality": "medium"}
                    },
                    {
                        "content": "Team structure and escalation procedures for handling complex customer issues.",
                        "source": "internal_procedures_fallback",
                        "score": 0.80,
                        "knowledge_base": "internal",
                        "metadata": {"category": "hr", "type": "fallback", "confidentiality": "medium"}
                    }
                ])
        
        # Sort by score and return top_k documents
        mock_documents.sort(key=lambda x: x['score'], reverse=True)
        return mock_documents[:top_k]
    
    def search_knowledge_base(self, query: str, user_role: str, chat_history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Search knowledge bases and generate response based on user role
        
        Args:
            query: User query
            user_role: User role (associate/customer)
            chat_history: Previous conversation history
            
        Returns:
            Response with generated text and metadata
        """
        try:
            # Retrieve relevant documents based on user role
            context_docs = self.retrieve_documents(query, user_role)
            
            # Get accessible knowledge bases for the user role
            if self.knowledge_base:
                accessible_kbs = [kb.value for kb in self.knowledge_base.get_accessible_kb_types(user_role)]
            else:
                accessible_kbs = ['general'] if user_role.lower() == 'customer' else ['general', 'internal']
            
            # Generate response using Gemini
            response_text = self.generate_response(
                query=query, 
                context_docs=context_docs, 
                chat_history=chat_history or [], 
                knowledge_bases=accessible_kbs
            )
            
            return {
                "response": response_text,
                "sources": context_docs,
                "knowledge_bases_used": accessible_kbs,
                "source_count": len(context_docs)
            }
            
        except Exception as e:
            logger.error(f"Error in search_knowledge_base: {e}")
            return {
                "response": "I apologize, but I'm experiencing technical difficulties. Please try your request again or contact support if the issue persists.",
                "sources": [],
                "knowledge_bases_used": [],
                "source_count": 0,
                "error": str(e)
            }
    
    def initialize_knowledge_base(self) -> bool:
        """
        Initialize knowledge base with sample data
        
        Returns:
            True if successful, False otherwise
        """
        if not self.knowledge_base:
            logger.error("Knowledge base manager not available")
            return False
        
        try:
            success = self.knowledge_base.initialize_sample_data()
            if success:
                logger.info("Knowledge base initialized with sample data")
            return success
            
        except Exception as e:
            logger.error(f"Failed to initialize knowledge base: {e}")
            return False
    
    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the knowledge base
        
        Returns:
            Dictionary with knowledge base statistics
        """
        if not self.knowledge_base:
            return {"status": "unavailable", "error": "Knowledge base manager not initialized"}
        
        try:
            return self.knowledge_base.get_collection_stats()
        except Exception as e:
            logger.error(f"Failed to get knowledge base stats: {e}")
            return {"status": "error", "error": str(e)}
    
    def process_query_with_ticket_creation(self, query: str, user_role: str, chat_history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process user query with intelligent ticket creation for complaints and service requests
        
        Args:
            query: User query
            user_role: User role (customer/associate)
            chat_history: Previous conversation history
            
        Returns:
            Comprehensive response with ticket creation if applicable
        """
        try:
            # Step 1: Classify intent and sentiment
            intent_analysis = self.intent_classifier.classify_intent(query)
            intent = intent_analysis.get("intent", "query")
            urgency = intent_analysis.get("urgency", "medium")
            sentiment = intent_analysis.get("sentiment", "neutral")
            
            # Step 2: Get regular RAG response first
            rag_response = self.search_knowledge_base(query, user_role, chat_history)
            base_response = rag_response["response"]
            
            # Step 3: Check if ticket creation is needed
            should_create_ticket = self.tool_framework.should_create_ticket(intent, user_role, query)
            
            ticket_info = None
            ticket_created = False
            validation_info = None
            
            if should_create_ticket:
                # Step 4: Handle complaint validation (if it's a complaint)
                if intent == "complaint":
                    validation_result = self.complaint_validator.validate_complaint(query, user_role)
                    validation_info = validation_result
                    
                    if not validation_result["is_valid"]:
                        # Invalid complaint - provide helpful response instead of creating ticket
                        helpful_response = self.complaint_validator.generate_invalid_complaint_response(query, validation_result)
                        return {
                            "response": helpful_response,
                            "original_rag_response": base_response,
                            "intent_analysis": intent_analysis,
                            "ticket_created": False,
                            "ticket_info": None,
                            "validation_info": validation_info,
                            "sources": rag_response.get("sources", []),
                            "knowledge_bases_used": rag_response.get("knowledge_bases_used", [])
                        }
                
                # Step 5: Create ticket for valid complaints/service requests
                ticket_type = self.tool_framework.determine_ticket_type(intent, user_role, query)
                
                if ticket_type:
                    # Extract title from query (first sentence or first 50 characters)
                    title = self._extract_title_from_query(query)
                    
                    # Prepare ticket data
                    ticket_data = {
                        "title": title,
                        "description": f"User query: {query}",
                        "urgency": urgency,
                        "sentiment": sentiment,
                        "user_query": query,
                        "user_role": user_role
                    }
                    
                    # Create the ticket using tool framework
                    tool_call = ToolCall(tool_type=ticket_type, parameters=ticket_data)
                    ticket_result = self.tool_framework.execute_tool(tool_call, user_role)
                    
                    if ticket_result.get("success"):
                        ticket_created = True
                        ticket_info = {
                            "local_ticket_id": ticket_result.get("local_ticket_id"),
                            "jira_issue_key": ticket_result.get("jira_issue_key"),
                            "ticket_type": intent,
                            "urgency": urgency,
                            "sentiment": sentiment
                        }
                        
                        # Enhance response with ticket information
                        ticket_message = f"\n\n**Ticket Created:** I've created a {intent.replace('_', ' ')} ticket for you.\n"
                        ticket_message += f"- Local Ticket ID: {ticket_info['local_ticket_id']}\n"
                        if ticket_info['jira_issue_key']:
                            ticket_message += f"- Jira Issue Key: {ticket_info['jira_issue_key']}\n"
                        ticket_message += f"- Urgency: {urgency.title()}\n"
                        ticket_message += "You can reference this ticket ID for future inquiries about this matter."
                        
                        enhanced_response = base_response + ticket_message
                    else:
                        # Ticket creation failed - still provide helpful response
                        enhanced_response = base_response + f"\n\nI attempted to create a ticket for your {intent.replace('_', ' ')}, but encountered an issue: {ticket_result.get('error', 'Unknown error')}. Please contact support directly if you need immediate assistance."
                else:
                    enhanced_response = base_response
            else:
                # No ticket needed - return regular RAG response
                enhanced_response = base_response
            
            return {
                "response": enhanced_response,
                "original_rag_response": base_response,
                "intent_analysis": intent_analysis,
                "ticket_created": ticket_created,
                "ticket_info": ticket_info,
                "validation_info": validation_info,
                "sources": rag_response.get("sources", []),
                "knowledge_bases_used": rag_response.get("knowledge_bases_used", []),
                "source_count": rag_response.get("source_count", 0)
            }
            
        except Exception as e:
            logger.error(f"Error in process_query_with_ticket_creation: {str(e)}")
            # Fallback to basic RAG response on error
            basic_response = self.search_knowledge_base(query, user_role, chat_history)
            return {
                "response": basic_response.get("response", "I apologize, but I'm experiencing technical difficulties."),
                "original_rag_response": basic_response.get("response", ""),
                "intent_analysis": {"intent": "query", "urgency": "medium", "sentiment": "neutral"},
                "ticket_created": False,
                "ticket_info": None,
                "validation_info": None,
                "sources": basic_response.get("sources", []),
                "knowledge_bases_used": basic_response.get("knowledge_bases_used", []),
                "source_count": basic_response.get("source_count", 0),
                "error": str(e)
            }
    
    def _extract_title_from_query(self, query: str) -> str:
        """Extract a suitable title from user query"""
        # Take first sentence or first 50 characters, whichever is shorter
        sentences = query.split('.')
        first_sentence = sentences[0].strip()
        
        if len(first_sentence) <= 50:
            return first_sentence
        else:
            # Truncate to 50 characters at word boundary
            words = first_sentence.split()
            title = ""
            for word in words:
                if len(title + " " + word) <= 47:  # Leave room for "..."
                    title = title + " " + word if title else word
                else:
                    break
            return title + "..." if len(first_sentence) > 50 else title