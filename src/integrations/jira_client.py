"""
Jira integration client for EchoPilot
Handles communication with Jira API for ticket management
"""

import os
from typing import Dict, Any, Optional


class JiraClient:
    """Client for Jira API integration"""
    
    def __init__(self):
        self.jira_url = os.getenv('JIRA_URL')
        self.jira_username = os.getenv('JIRA_USERNAME')
        self.jira_api_token = os.getenv('JIRA_API_TOKEN')
        self.project_key = os.getenv('JIRA_PROJECT_KEY', 'CS')  # Customer Support
    
    def create_issue(self, issue_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new issue in Jira
        
        Args:
            issue_data: Dictionary containing issue information
            
        Returns:
            Created issue key or None if failed
        """
        # Placeholder implementation
        # TODO: Implement actual Jira API integration
        
        if not all([self.jira_url, self.jira_username, self.jira_api_token]):
            print("Warning: Jira credentials not configured")
            return None
        
        # Mock issue creation for prototype
        mock_issue_key = f"{self.project_key}-{hash(issue_data.get('summary', ''))% 1000:03d}"
        
        return mock_issue_key
    
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
            complaint_data: Complaint information
            
        Returns:
            Created issue key or None if failed
        """
        issue_data = {
            "project": {"key": self.project_key},
            "summary": complaint_data.get('title', 'Customer Complaint'),
            "description": complaint_data.get('description', ''),
            "issuetype": {"name": "Bug"},  # Map complaints to bug type
            "priority": {"name": self._map_urgency_to_priority(complaint_data.get('urgency', 'medium'))},
            "labels": ["complaint", f"sentiment-{complaint_data.get('sentiment', 'neutral')}"]
        }
        
        return self.create_issue(issue_data)
    
    def _map_urgency_to_priority(self, urgency: str) -> str:
        """Map urgency level to Jira priority"""
        mapping = {
            "high": "High",
            "medium": "Medium", 
            "low": "Low"
        }
        return mapping.get(urgency, "Medium")