"""
Gemini API client for EchoPilot
Handles communication with Google Gemini API for response generation
"""

import os
from typing import Dict, Any, List, Optional
import logging
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Configure logging
logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for Google Gemini API integration"""
    
    def __init__(self):
        """Initialize Gemini client with API key and safety settings"""
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.model = None
        
        if self.api_key:
            try:
                # Configure the API
                genai.configure(api_key=self.api_key)
                
                # Initialize the model with safety settings (Updated to Gemini 2.0 Flash)
                self.model = genai.GenerativeModel(
                    model_name='gemini-2.0-flash-exp',
                    safety_settings={
                        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    }
                )
                logger.info("Gemini client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
                self.model = None
        else:
            logger.warning("GEMINI_API_KEY not found in environment variables")
        
    def generate_response(self, prompt: str, context: str = "", temperature: float = 0.7) -> str:
        """
        Generate response using Gemini API
        
        Args:
            prompt: Input prompt
            context: Additional context for the model
            temperature: Response creativity (0.0 to 1.0)
            
        Returns:
            Generated response text
        """
        if not self.model:
            if not self.api_key:
                return "I apologize, but I'm unable to provide AI-generated responses because the Gemini API key is not configured. Please contact your administrator to set up the GEMINI_API_KEY environment variable."
            else:
                return "I'm experiencing technical difficulties with the AI service. Please try again later or contact support."
        
        try:
            # Combine context and prompt if context is provided
            full_prompt = prompt
            if context.strip():
                full_prompt = f"Context: {context}\n\nUser Query: {prompt}\n\nPlease provide a helpful response based on the context above."
            
            # Generate response
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=2048,  # Increased for better responses
                    top_p=0.8,
                    top_k=10
                )
            )
            
            if response.text:
                return response.text.strip()
            else:
                return "I apologize, but I couldn't generate a response. This might be due to safety filters. Please try rephrasing your question."
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I encountered an error while processing your request. Please try again later."
    
    def generate_rag_response(self, user_query: str, context_documents: List[Dict[str, Any]], 
                            knowledge_bases: List[str], chat_history: List[Dict[str, Any]] = None) -> str:
        """
        Generate a RAG (Retrieval Augmented Generation) response
        
        Args:
            user_query: User's question or request
            context_documents: Retrieved documents providing context
            knowledge_bases: List of knowledge bases used
            chat_history: Previous conversation history
            
        Returns:
            Generated response based on context
        """
        if not self.model:
            return self.generate_response(user_query)  # Falls back to error message
        
        try:
            # Build context from documents
            context_text = ""
            if context_documents:
                context_text = "Relevant Information:\n"
                for i, doc in enumerate(context_documents[:3], 1):  # Limit to 3 most relevant
                    content = doc.get('content', '')[:500]  # Limit doc length
                    source = doc.get('source', 'Unknown')
                    context_text += f"{i}. {content} (Source: {source})\n\n"
            
            # Build chat history context
            history_text = ""
            if chat_history:
                recent_history = chat_history[-4:]  # Last 2 exchanges
                history_text = "Recent Conversation:\n"
                for msg in recent_history:
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')[:200]  # Limit length
                    history_text += f"{role.title()}: {content}\n"
                history_text += "\n"
            
            # Create comprehensive prompt for customer success context
            prompt = f"""You are EchoPilot, a helpful customer success assistant. You have access to company knowledge bases and are here to help with queries, complaints, and service requests.

Available Knowledge Bases: {', '.join(knowledge_bases) if knowledge_bases else 'General knowledge'}

{history_text}{context_text}Current User Query: {user_query}

Instructions:
- Provide accurate, helpful responses based on the context above
- If the context doesn't contain relevant information, acknowledge this and provide general guidance
- For complaints, be empathetic and offer to escalate or create a ticket if needed
- For service requests, be helpful and actionable
- Be concise but thorough in your responses
- Maintain a professional, friendly tone

Response:"""
            
            return self.generate_response(prompt, temperature=0.3)  # Lower temperature for consistency
            
        except Exception as e:
            logger.error(f"Error generating RAG response: {e}")
            return "I apologize for the technical difficulty. Let me try to help you with a basic response to your question."
    
    def summarize_conversation(self, chat_history: List[Dict[str, Any]]) -> str:
        """
        Generate a summary of a chat conversation
        
        Args:
            chat_history: List of chat messages
            
        Returns:
            Conversation summary
        """
        if not self.model or not chat_history:
            return "No conversation to summarize"
        
        try:
            # Build conversation text
            conversation_text = ""
            for msg in chat_history:
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                conversation_text += f"{role.title()}: {content}\n"
            
            prompt = f"""Please provide a concise summary of the following customer service conversation. Focus on:
1. Main topics discussed
2. Issues raised or questions asked
3. Any action items or follow-ups needed
4. Overall sentiment and resolution status

Conversation:
{conversation_text}

Summary:"""
            
            return self.generate_response(prompt, temperature=0.2)
            
        except Exception as e:
            logger.error(f"Error summarizing conversation: {e}")
            return "Unable to generate conversation summary"