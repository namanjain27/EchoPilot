#!/usr/bin/env python3
"""
Test script for separate chat modes functionality
Tests role-based chat separation without Streamlit UI
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from auth.session_handler import SessionHandler
from auth.role_manager import UserRole

def test_role_based_chat_separation():
    """Test that chat histories are properly separated by role"""
    print("🧪 Testing Role-Based Chat Separation...")
    
    # Mock Streamlit session state
    class MockSessionState:
        def __init__(self):
            self.data = {}
        
        def __getattr__(self, name):
            return self.data.get(name)
        
        def __setattr__(self, name, value):
            if name == 'data':
                super().__setattr__(name, value)
            else:
                self.data[name] = value
        
        def __contains__(self, name):
            return name in self.data
        
        def __delitem__(self, key):
            if key in self.data:
                del self.data[key]
    
    # Mock streamlit session state
    import streamlit as st
    st.session_state = MockSessionState()
    
    # Create session handler
    handler = SessionHandler()
    
    # Test 1: Initial state
    print("✅ Test 1: Initial state check")
    assert 'chat_histories' in st.session_state
    assert st.session_state.chat_histories == {"associate": [], "customer": []}
    print("   ✓ Chat histories initialized correctly")
    
    # Test 2: Role-specific message storage
    print("✅ Test 2: Role-specific message storage")
    
    # Set role to Associate and add messages
    handler.set_user_role(UserRole.ASSOCIATE)
    handler.add_message_for_current_role({"role": "user", "content": "Associate message 1"})
    handler.add_message_for_current_role({"role": "assistant", "content": "Associate response 1"})
    
    # Switch to Customer and add different messages
    handler.set_user_role(UserRole.CUSTOMER)
    handler.add_message_for_current_role({"role": "user", "content": "Customer message 1"})
    handler.add_message_for_current_role({"role": "assistant", "content": "Customer response 1"})
    
    # Verify separation
    associate_history = handler.get_chat_history(UserRole.ASSOCIATE)
    customer_history = handler.get_chat_history(UserRole.CUSTOMER)
    
    assert len(associate_history) == 2
    assert len(customer_history) == 2
    assert associate_history[0]["content"] == "Associate message 1"
    assert customer_history[0]["content"] == "Customer message 1"
    print("   ✓ Messages stored in correct role-specific histories")
    
    # Test 3: Role switching preserves context
    print("✅ Test 3: Role switching preserves context")
    
    # Switch back to Associate
    handler.set_user_role(UserRole.ASSOCIATE)
    current_history = handler.get_current_role_chat_history()
    assert len(current_history) == 2
    assert current_history[0]["content"] == "Associate message 1"
    print("   ✓ Associate context preserved after role switch")
    
    # Switch back to Customer
    handler.set_user_role(UserRole.CUSTOMER)
    current_history = handler.get_current_role_chat_history()
    assert len(current_history) == 2
    assert current_history[0]["content"] == "Customer message 1"
    print("   ✓ Customer context preserved after role switch")
    
    # Test 4: Role-specific clearing
    print("✅ Test 4: Role-specific clearing")
    
    # Clear only current role (Customer)
    handler.clear_current_role_chat_history()
    customer_history = handler.get_current_role_chat_history()
    associate_history = handler.get_chat_history(UserRole.ASSOCIATE)
    
    assert len(customer_history) == 0
    assert len(associate_history) == 2  # Should be unchanged
    print("   ✓ Only current role's history cleared, other role preserved")
    
    # Test 5: Clear all histories
    print("✅ Test 5: Clear all histories")
    
    # Add a message back to customer
    handler.add_message_for_current_role({"role": "user", "content": "New customer message"})
    
    # Clear all
    handler.clear_all_chat_histories()
    
    associate_history = handler.get_chat_history(UserRole.ASSOCIATE)
    customer_history = handler.get_chat_history(UserRole.CUSTOMER)
    
    assert len(associate_history) == 0
    assert len(customer_history) == 0
    print("   ✓ All chat histories cleared successfully")
    
    # Test 6: Backward compatibility migration
    print("✅ Test 6: Backward compatibility migration")
    
    # Simulate old single chat_history
    st.session_state.chat_history = [
        {"role": "user", "content": "Old message 1"},
        {"role": "assistant", "content": "Old response 1"}
    ]
    
    # Re-initialize should migrate old history
    handler._initialize_session_state()
    
    # Old history should be moved to customer role
    customer_history = handler.get_chat_history(UserRole.CUSTOMER)
    assert len(customer_history) == 2
    assert customer_history[0]["content"] == "Old message 1"
    assert 'chat_history' not in st.session_state
    print("   ✓ Old chat history migrated to customer role successfully")
    
    print("\n🎉 All tests passed! Role-based chat separation is working correctly.")
    return True

def test_role_switching_and_persistence():
    """Test role switching maintains separate chat histories"""
    print("\n🧪 Testing Role Switching and Chat Persistence...")
    
    import streamlit as st
    
    handler = SessionHandler()
    
    # Test scenario: Switch between roles multiple times
    print("✅ Test: Multiple role switches with chat persistence")
    
    # Start as Associate, add messages
    handler.set_user_role(UserRole.ASSOCIATE)
    handler.add_message_for_current_role({"role": "user", "content": "Associate question 1"})
    handler.add_message_for_current_role({"role": "assistant", "content": "Associate answer 1"})
    
    # Switch to Customer, add messages
    handler.set_user_role(UserRole.CUSTOMER)
    handler.add_message_for_current_role({"role": "user", "content": "Customer question 1"})
    
    # Switch back to Associate, verify history persisted
    handler.set_user_role(UserRole.ASSOCIATE)
    associate_history = handler.get_current_role_chat_history()
    assert len(associate_history) == 2
    assert "Associate question 1" in associate_history[0]["content"]
    print("   ✓ Associate history persisted across role switches")
    
    # Add more Associate messages
    handler.add_message_for_current_role({"role": "user", "content": "Associate question 2"})
    
    # Switch back to Customer, verify history persisted
    handler.set_user_role(UserRole.CUSTOMER)
    customer_history = handler.get_current_role_chat_history()
    assert len(customer_history) == 1
    assert "Customer question 1" in customer_history[0]["content"]
    print("   ✓ Customer history persisted across role switches")
    
    # Verify Associate history still intact
    associate_history = handler.get_chat_history(UserRole.ASSOCIATE)
    assert len(associate_history) == 3
    print("   ✓ Associate history remained intact while in Customer mode")
    
    print("✅ Role switching and persistence working correctly")
    return True

if __name__ == "__main__":
    try:
        test_role_based_chat_separation()
        test_role_switching_and_persistence()
        print("\n🎊 All functionality tests completed successfully!")
        print("✅ The separate chat modes implementation is working correctly.")
        print("✅ Phase 3 implementation complete with simplified UI design.")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)