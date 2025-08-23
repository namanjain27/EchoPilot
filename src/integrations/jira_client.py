"""
Jira integration client for EchoPilot
Handles communication with Jira API for ticket management
"""

import os
import requests
import json
import logging
from typing import Dict, Any, Optional
from base64 import b64encode


class JiraClient:
    """Client for Jira API integration"""
    
    def __init__(self):
        self.jira_url = os.getenv('JIRA_URL')
        self.jira_username = os.getenv('JIRA_USERNAME')
        self.jira_api_token = os.getenv('JIRA_API_TOKEN')
        self.project_key = os.getenv('JIRA_PROJECT_KEY', 'CS')  # Customer Support
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Validate configuration
        self.is_configured = all([self.jira_url, self.jira_username, self.jira_api_token])
        
        if self.is_configured:
            # Setup authentication headers
            auth_string = f"{self.jira_username}:{self.jira_api_token}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = b64encode(auth_bytes).decode('ascii')
            
            self.headers = {
                'Authorization': f'Basic {auth_b64}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            self.logger.info("Jira client initialized successfully")
        else:
            self.logger.warning("Jira client not properly configured - missing credentials")
    
    def create_issue(self, issue_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new issue in Jira
        
        Args:
            issue_data: Dictionary containing issue information with fields structure
            
        Returns:
            Created issue key or None if failed
        """
        if not self.is_configured:
            self.logger.warning("Jira not configured - creating mock ticket")
            # Mock issue creation for development/testing
            mock_issue_key = f"{self.project_key}-{hash(str(issue_data))% 1000:03d}"
            return mock_issue_key
        
        try:
            url = f"{self.jira_url}/rest/api/3/issue"
            
            # Create the issue payload
            payload = {
                "fields": issue_data
            }
            
            self.logger.info(f"Creating Jira issue with payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(url, headers=self.headers, data=json.dumps(payload), timeout=30)
            
            if response.status_code == 201:
                response_data = response.json()
                issue_key = response_data.get('key')
                self.logger.info(f"Successfully created Jira issue: {issue_key}")
                return issue_key
            else:
                self.logger.error(f"Failed to create Jira issue. Status: {response.status_code}, Response: {response.text}")
                return None
                
        except requests.RequestException as e:
            self.logger.error(f"Request error creating Jira issue: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error creating Jira issue: {str(e)}")
            return None
    
    def get_issue(self, issue_key: str) -> Optional[Dict[str, Any]]:
        """
        Get issue details from Jira
        
        Args:
            issue_key: Jira issue key
            
        Returns:
            Issue details or None if not found
        """
        # Placeholder implementation
        # TODO: Implement actual Jira API call
        
        return {
            "key": issue_key,
            "summary": "Sample issue",
            "status": "Open",
            "created": "2024-01-01T00:00:00Z"
        }
    
    def update_issue(self, issue_key: str, update_data: Dict[str, Any]) -> bool:
        """
        Update issue in Jira
        
        Args:
            issue_key: Jira issue key
            update_data: Data to update
            
        Returns:
            True if successful, False otherwise
        """
        # Placeholder implementation
        # TODO: Implement actual Jira API call
        
        return True
    
    def create_complaint_ticket(self, complaint_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a complaint ticket in Jira
        
        Args:
            complaint_data: Complaint information with keys: title, description, urgency, sentiment, user_query
            
        Returns:
            Created issue key or None if failed
        """
        # Build description with original user query
        description = f"**Customer Complaint:**\n{complaint_data.get('description', '')}\n\n"
        description += f"**Original User Query:**\n{complaint_data.get('user_query', 'Not provided')}\n\n"
        description += f"**Urgency:** {complaint_data.get('urgency', 'medium')}\n"
        description += f"**Sentiment:** {complaint_data.get('sentiment', 'neutral')}\n"
        description += f"**User Role:** {complaint_data.get('user_role', 'customer')}"
        
        issue_fields = {
            "project": {"key": self.project_key},
            "summary": complaint_data.get('title', 'Customer Complaint'),
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": description}]
                    }
                ]
            },
            "issuetype": {"name": "Task"},  # Using Task as it's more universally available
            "priority": {"name": self._map_urgency_to_priority(complaint_data.get('urgency', 'medium'))},
            "labels": ["complaint", f"sentiment-{complaint_data.get('sentiment', 'neutral')}"]
        }
        
        return self.create_issue(issue_fields)
    
    def create_service_request_ticket(self, request_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a service request ticket in Jira
        
        Args:
            request_data: Service request information
            
        Returns:
            Created issue key or None if failed
        """
        description = f"**Service Request:**\n{request_data.get('description', '')}\n\n"
        description += f"**Original User Query:**\n{request_data.get('user_query', 'Not provided')}\n\n"
        description += f"**Urgency:** {request_data.get('urgency', 'medium')}\n"
        description += f"**User Role:** {request_data.get('user_role', 'customer')}"
        
        issue_fields = {
            "project": {"key": self.project_key},
            "summary": request_data.get('title', 'Customer Service Request'),
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": description}]
                    }
                ]
            },
            "issuetype": {"name": "Task"},
            "priority": {"name": self._map_urgency_to_priority(request_data.get('urgency', 'medium'))},
            "labels": ["service-request", f"urgency-{request_data.get('urgency', 'medium')}"]
        }
        
        return self.create_issue(issue_fields)
    
    def create_feature_request_ticket(self, feature_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a feature request ticket in Jira (Associates only)
        
        Args:
            feature_data: Feature request information
            
        Returns:
            Created issue key or None if failed
        """
        description = f"**Feature Request:**\n{feature_data.get('description', '')}\n\n"
        description += f"**Original Request:**\n{feature_data.get('user_query', 'Not provided')}\n\n"
        description += f"**Priority:** {feature_data.get('urgency', 'medium')}\n"
        description += f"**Requested by:** Associate"
        
        issue_fields = {
            "project": {"key": self.project_key},
            "summary": feature_data.get('title', 'Feature Request'),
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": description}]
                    }
                ]
            },
            "issuetype": {"name": "Story"},  # Feature requests as stories
            "priority": {"name": self._map_urgency_to_priority(feature_data.get('urgency', 'medium'))},
            "labels": ["feature-request", "associate-request"]
        }
        
        return self.create_issue(issue_fields)
    
    def _map_urgency_to_priority(self, urgency: str) -> str:
        """Map urgency level to Jira priority"""
        mapping = {
            "high": "High",
            "medium": "Medium", 
            "low": "Low"
        }
        return mapping.get(urgency, "Medium")