from jira import JIRA
import os
from dotenv import load_dotenv
from typing import List

class JiraTool:

    def __init__(self):
        load_dotenv()
        host = os.environ.get("JIRA_URL")
        api_token =  os.environ.get("JIRA_API_TOKEN")
        project_key = os.environ.get("JIRA_PROJECT_KEY")
        email = os.environ.get("JIRA_EMAIL")

        jira = JIRA(
                server=host,
                basic_auth=(email, api_token)
            )
        
        # issue_types = jira.issue_types()
        # for issue_type in issue_types print(f"{issue_type.name} \n") 
        # # lists the issue types [Subtask,Task,Bug,Story,Epic]
        server_info = jira.server_info()
        print("Connected to Jira: ", server_info['baseUrl'])

    def create_ticket(summary:str, desc:str, labels:List[str]) -> str:
        """creates a jira ticket for service request, complaints and feature request"""
        # build the issue_data
        ## input the ticket parameters - summary, description, labels
        ## issuetype is fixed to Story
        issue_data = {
            "project": {"key": project_key},
            "summary": summary,
            "description": desc,
            "issuetype": {"name": "Story"},
            "labels": labels # ["customer", "complaint"]
        }
        try:
            new_issue = jira.create_issue(fields=issue_data)
            print("Issue created successfully! with issue key:", new_issue.key) # share this with the user in the chat
            return new_issue.key
        except Exception as e:
            print("Failed to create issue:", str(e))
            return None

