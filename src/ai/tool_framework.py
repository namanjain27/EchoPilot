"""
Tool calling framework for EchoPilot
Handles AI-driven tool calls for ticket creation and validation
"""

import logging
from typing import Dict, Any, Optional, List, Callable, TYPE_CHECKING
from enum import Enum
from dataclasses import dataclass
import json

from src.integrations.jira_client import JiraClient
from src.integrations.ticket_manager import TicketManager

if TYPE_CHECKING:
    from .rag_engine import RAGEngine


class ToolType(Enum):
    """Types of available tools"""
    CREATE_COMPLAINT_TICKET = "create_complaint_ticket"
    CREATE_SERVICE_REQUEST_TICKET = "create_service_request_ticket"
    CREATE_FEATURE_REQUEST_TICKET = "create_feature_request_ticket"
    VALIDATE_COMPLAINT = "validate_complaint"
    SEARCH_KNOWLEDGE_BASE = "search_knowledge_base"


@dataclass
class ToolCall:
    """Represents a tool call with parameters"""
    tool_type: ToolType
    parameters: Dict[str, Any]
    reasoning: str = ""


class ToolFramework:
    """Framework for AI-driven tool calling"""
    
    def __init__(self, rag_engine: "RAGEngine", ticket_manager: TicketManager, jira_client: JiraClient):
        self.rag_engine = rag_engine
        self.ticket_manager = ticket_manager
        self.jira_client = jira_client
        self.logger = logging.getLogger(__name__)
        
        # Register available tools
        self.tools: Dict[ToolType, Callable] = {
            ToolType.CREATE_COMPLAINT_TICKET: self._create_complaint_ticket,
            ToolType.CREATE_SERVICE_REQUEST_TICKET: self._create_service_request_ticket,
            ToolType.CREATE_FEATURE_REQUEST_TICKET: self._create_feature_request_ticket,
            ToolType.VALIDATE_COMPLAINT: self._validate_complaint,
            ToolType.SEARCH_KNOWLEDGE_BASE: self._search_knowledge_base,
        }
    
    def should_create_ticket(self, intent: str, user_role: str, user_query: str) -> bool:
        """
        Determine if a ticket should be created based on intent and role
        
        Args:
            intent: Classified intent (complaint, service_request, query)
            user_role: User role (customer, associate)  
            user_query: Original user query
            
        Returns:
            True if ticket should be created
        """
        # Ticket creation rules based on implementation plan
        if intent == "complaint":
            return True  # Always create tickets for complaints
        elif intent == "service_request":
            return True  # Always create tickets for service requests
        elif intent == "query" and user_role == "associate":
            # Associates can create feature requests for queries
            feature_keywords = ["feature", "enhancement", "improve", "add", "new", "request"]
            return any(keyword in user_query.lower() for keyword in feature_keywords)
        
        return False
    
    def determine_ticket_type(self, intent: str, user_role: str, user_query: str) -> Optional[ToolType]:
        """
        Determine the appropriate ticket type based on intent and role
        
        Args:
            intent: Classified intent
            user_role: User role
            user_query: Original user query
            
        Returns:
            Appropriate ToolType for ticket creation or None
        """
        if intent == "complaint":
            return ToolType.CREATE_COMPLAINT_TICKET
        elif intent == "service_request":
            return ToolType.CREATE_SERVICE_REQUEST_TICKET
        elif intent == "query" and user_role == "associate":
            # Check if it's a feature request
            feature_keywords = ["feature", "enhancement", "improve", "add", "new", "request"]
            if any(keyword in user_query.lower() for keyword in feature_keywords):
                return ToolType.CREATE_FEATURE_REQUEST_TICKET
        
        return None
    
    def execute_tool(self, tool_call: ToolCall, user_role: str) -> Dict[str, Any]:
        """
        Execute a tool call
        
        Args:
            tool_call: ToolCall object with type and parameters
            user_role: User role for access control
            
        Returns:
            Tool execution result
        """
        try:
            if tool_call.tool_type not in self.tools:
                return {
                    "success": False,
                    "error": f"Unknown tool type: {tool_call.tool_type}"
                }
            
            # Check role permissions
            if not self._check_tool_permission(tool_call.tool_type, user_role):
                return {
                    "success": False,
                    "error": f"User role '{user_role}' not authorized for tool '{tool_call.tool_type.value}'"
                }
            
            # Execute the tool
            tool_function = self.tools[tool_call.tool_type]
            result = tool_function(tool_call.parameters, user_role)
            
            self.logger.info(f"Successfully executed tool: {tool_call.tool_type.value}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing tool {tool_call.tool_type.value}: {str(e)}")
            return {
                "success": False,
                "error": f"Tool execution failed: {str(e)}"
            }
    
    def _check_tool_permission(self, tool_type: ToolType, user_role: str) -> bool:
        """Check if user has permission to use the tool"""
        role_permissions = {
            "customer": [
                ToolType.CREATE_COMPLAINT_TICKET,
                ToolType.CREATE_SERVICE_REQUEST_TICKET,
                ToolType.VALIDATE_COMPLAINT,
                ToolType.SEARCH_KNOWLEDGE_BASE
            ],
            "associate": [  # Associates have access to all tools
                ToolType.CREATE_COMPLAINT_TICKET,
                ToolType.CREATE_SERVICE_REQUEST_TICKET,
                ToolType.CREATE_FEATURE_REQUEST_TICKET,
                ToolType.VALIDATE_COMPLAINT,
                ToolType.SEARCH_KNOWLEDGE_BASE
            ]
        }
        
        return tool_type in role_permissions.get(user_role, [])
    
    def _create_complaint_ticket(self, parameters: Dict[str, Any], user_role: str) -> Dict[str, Any]:
        """Create a complaint ticket"""
        required_fields = ["title", "description", "urgency", "sentiment", "user_query"]
        
        if not all(field in parameters for field in required_fields):
            missing = [f for f in required_fields if f not in parameters]
            return {
                "success": False,
                "error": f"Missing required fields: {missing}"
            }
        
        # Add user role to parameters
        parameters["user_role"] = user_role
        parameters["type"] = "complaint"
        
        # Create local ticket first
        local_ticket_id = self.ticket_manager.create_ticket(parameters)
        
        # Create Jira ticket
        jira_issue_key = self.jira_client.create_complaint_ticket(parameters)
        
        return {
            "success": True,
            "local_ticket_id": local_ticket_id,
            "jira_issue_key": jira_issue_key,
            "message": f"Complaint ticket created successfully. Local ID: {local_ticket_id}, Jira Key: {jira_issue_key}"
        }
    
    def _create_service_request_ticket(self, parameters: Dict[str, Any], user_role: str) -> Dict[str, Any]:
        """Create a service request ticket"""
        required_fields = ["title", "description", "urgency", "user_query"]
        
        if not all(field in parameters for field in required_fields):
            missing = [f for f in required_fields if f not in parameters]
            return {
                "success": False,
                "error": f"Missing required fields: {missing}"
            }
        
        parameters["user_role"] = user_role
        parameters["type"] = "service_request"
        
        # Create local ticket
        local_ticket_id = self.ticket_manager.create_ticket(parameters)
        
        # Create Jira ticket
        jira_issue_key = self.jira_client.create_service_request_ticket(parameters)
        
        return {
            "success": True,
            "local_ticket_id": local_ticket_id,
            "jira_issue_key": jira_issue_key,
            "message": f"Service request ticket created successfully. Local ID: {local_ticket_id}, Jira Key: {jira_issue_key}"
        }
    
    def _create_feature_request_ticket(self, parameters: Dict[str, Any], user_role: str) -> Dict[str, Any]:
        """Create a feature request ticket (Associates only)"""
        if user_role != "associate":
            return {
                "success": False,
                "error": "Feature requests can only be created by associates"
            }
        
        required_fields = ["title", "description", "urgency", "user_query"]
        
        if not all(field in parameters for field in required_fields):
            missing = [f for f in required_fields if f not in parameters]
            return {
                "success": False,
                "error": f"Missing required fields: {missing}"
            }
        
        parameters["user_role"] = user_role
        parameters["type"] = "feature_request"
        
        # Create local ticket
        local_ticket_id = self.ticket_manager.create_ticket(parameters)
        
        # Create Jira ticket
        jira_issue_key = self.jira_client.create_feature_request_ticket(parameters)
        
        return {
            "success": True,
            "local_ticket_id": local_ticket_id,
            "jira_issue_key": jira_issue_key,
            "message": f"Feature request ticket created successfully. Local ID: {local_ticket_id}, Jira Key: {jira_issue_key}"
        }
    
    def _validate_complaint(self, parameters: Dict[str, Any], user_role: str) -> Dict[str, Any]:
        """Validate complaint against knowledge base"""
        complaint_text = parameters.get("complaint_text", "")
        
        if not complaint_text:
            return {
                "success": False,
                "error": "Complaint text is required for validation"
            }
        
        try:
            # Search knowledge base for relevant information
            relevant_docs = self.rag_engine.retrieve_documents(complaint_text, user_role)
            
            if not relevant_docs:
                return {
                    "success": True,
                    "is_valid": True,  # If no relevant docs found, assume complaint is valid
                    "reasoning": "No relevant information found in knowledge base to validate complaint",
                    "relevant_documents": []
                }
            
            # For now, we'll consider complaints valid unless explicitly contradicted
            # This can be enhanced with more sophisticated validation logic
            return {
                "success": True,
                "is_valid": True,
                "reasoning": f"Found {len(relevant_docs)} relevant documents for review",
                "relevant_documents": [doc.get("content", "")[:200] + "..." for doc in relevant_docs[:3]]
            }
            
        except Exception as e:
            self.logger.error(f"Error validating complaint: {str(e)}")
            return {
                "success": False,
                "error": f"Validation failed: {str(e)}"
            }
    
    def _search_knowledge_base(self, parameters: Dict[str, Any], user_role: str) -> Dict[str, Any]:
        """Search knowledge base for information"""
        query = parameters.get("query", "")
        
        if not query:
            return {
                "success": False,
                "error": "Query is required for knowledge base search"
            }
        
        try:
            documents = self.rag_engine.retrieve_documents(query, user_role)
            
            return {
                "success": True,
                "documents": documents[:5],  # Return top 5 documents
                "count": len(documents)
            }
            
        except Exception as e:
            self.logger.error(f"Error searching knowledge base: {str(e)}")
            return {
                "success": False,
                "error": f"Search failed: {str(e)}"
            }
    
    def get_available_tools(self, user_role: str) -> List[str]:
        """Get list of tools available to the user role"""
        available = []
        for tool_type in ToolType:
            if self._check_tool_permission(tool_type, user_role):
                available.append(tool_type.value)
        
        return available