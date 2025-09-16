#!/usr/bin/env python3
"""
Test script for session flow: start -> chat -> history -> end
This tests APIs 3, 4, 5, 6, 7 from the SDK plan
"""

import requests
import json
import sys
import time

BASE_URL = "http://localhost:8000/api/v1"

def test_session_flow():
    """Test the complete session flow"""
    print("🧪 Testing complete session flow...")
    
    # Step 1: Start a session
    print("\n1️⃣ Starting new session...")
    start_response = requests.post(f"{BASE_URL}/session/start")
    
    if start_response.status_code != 200:
        print(f"❌ Session start failed: {start_response.text}")
        return False
    
    session_data = start_response.json()
    session_id = session_data["session_id"]
    print(f"✅ Session started: {session_id}")
    print(f"   Agent initialized: {session_data['agent_initialized']}")
    
    # Step 2: Send a chat message
    print(f"\n2️⃣ Sending chat message to session {session_id}...")
    chat_data = {
        "message": "Hello, this is a test message for the API",
        "session_id": session_id
    }
    
    chat_response = requests.post(f"{BASE_URL}/chat", data=chat_data)
    
    if chat_response.status_code != 200:
        print(f"❌ Chat failed: {chat_response.text}")
        return False
    
    chat_result = chat_response.json()
    print(f"✅ Chat response received")
    print(f"   Response: {chat_result['response'][:100]}...")
    print(f"   Files processed: {chat_result['files_processed']}")
    
    # Step 3: Get session history
    print(f"\n3️⃣ Getting session history for {session_id}...")
    history_response = requests.get(f"{BASE_URL}/session/history", params={"session_id": session_id})
    
    if history_response.status_code != 200:
        print(f"❌ Session history failed: {history_response.text}")
        return False
    
    history_data = history_response.json()
    print(f"✅ Session history retrieved")
    print(f"   Message count: {history_data['message_count']}")
    
    for i, msg in enumerate(history_data['messages']):
        print(f"   Message {i+1}: [{msg['role']}] {msg['content'][:50]}...")
    
    # Step 4: Get KB status (API 4)
    print(f"\n4️⃣ Getting knowledge base status...")
    kb_status_response = requests.get(f"{BASE_URL}/knowledge-base/status")
    
    if kb_status_response.status_code != 200:
        print(f"❌ KB status failed: {kb_status_response.text}")
        return False
    
    kb_data = kb_status_response.json()
    print(f"✅ KB status retrieved")
    print(f"   Status: {kb_data['status']}")
    print(f"   Document count: {kb_data['document_count']}")
    
    # Step 5: End the session
    print(f"\n5️⃣ Ending session {session_id}...")
    end_data = {"session_id": session_id}
    end_response = requests.post(f"{BASE_URL}/session/end", json=end_data)
    
    if end_response.status_code != 200:
        print(f"❌ Session end failed: {end_response.text}")
        return False
    
    end_result = end_response.json()
    print(f"✅ Session ended successfully")
    print(f"   Message: {end_result['message']}")
    
    # Step 6: Verify session is gone (try to get history)
    print(f"\n6️⃣ Verifying session cleanup...")
    cleanup_response = requests.get(f"{BASE_URL}/session/history", params={"session_id": session_id})
    
    if cleanup_response.status_code == 404:
        print("✅ Session properly cleaned up (404 as expected)")
    else:
        print(f"⚠️ Session might not be cleaned up: {cleanup_response.status_code}")
    
    print(f"\n🎉 Complete session flow test passed!")
    return True

def test_health_check():
    """Test the health check endpoint (API 8)"""
    print("\n🏥 Testing health check...")
    
    health_response = requests.get(f"{BASE_URL}/health")
    
    if health_response.status_code != 200:
        print(f"❌ Health check failed: {health_response.text}")
        return False
    
    health_data = health_response.json()
    print(f"✅ Health check passed")
    print(f"   Status: {health_data['status']}")
    print(f"   Services: {health_data['services']}")
    
    return True

if __name__ == "__main__":
    print("🚀 Testing EchoPilot API Session Flow")
    print("=" * 50)
    
    try:
        # Test health check first
        if not test_health_check():
            sys.exit(1)
            
        # Test complete session flow
        if not test_session_flow():
            sys.exit(1)
            
        print("\n🎯 All tests passed successfully!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API server. Make sure it's running on http://localhost:8000")
        print("   Start with: python3 -m api.main")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)