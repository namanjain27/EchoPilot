"""
Test dataset for intent classification validation
Contains 50+ labeled examples for testing classifier accuracy
"""

TEST_CASES = [
    # Query examples (informational requests)
    {"message": "What are your business hours?", "intent": "query", "urgency": "low", "sentiment": "neutral"},
    {"message": "How do I reset my password?", "intent": "query", "urgency": "medium", "sentiment": "neutral"},
    {"message": "Can you explain this feature to me?", "intent": "query", "urgency": "low", "sentiment": "neutral"},
    {"message": "What's the difference between these plans?", "intent": "query", "urgency": "low", "sentiment": "neutral"},
    {"message": "How does billing work?", "intent": "query", "urgency": "medium", "sentiment": "neutral"},
    {"message": "Where can I find the documentation?", "intent": "query", "urgency": "low", "sentiment": "neutral"},
    {"message": "What integrations do you support?", "intent": "query", "urgency": "low", "sentiment": "neutral"},
    {"message": "How do I contact support?", "intent": "query", "urgency": "medium", "sentiment": "neutral"},
    {"message": "What's your refund policy?", "intent": "query", "urgency": "medium", "sentiment": "neutral"},
    {"message": "Can you help me understand this error message?", "intent": "query", "urgency": "medium", "sentiment": "neutral"},
    {"message": "Is this feature available in my plan?", "intent": "query", "urgency": "low", "sentiment": "neutral"},
    {"message": "How long does it take to process requests?", "intent": "query", "urgency": "low", "sentiment": "neutral"},
    {"message": "What are the system requirements?", "intent": "query", "urgency": "low", "sentiment": "neutral"},
    {"message": "Do you have API documentation?", "intent": "query", "urgency": "low", "sentiment": "neutral"},
    {"message": "How secure is your platform?", "intent": "query", "urgency": "medium", "sentiment": "neutral"},
    
    # Complaint examples (expressions of dissatisfaction)
    {"message": "This feature is completely broken!", "intent": "complaint", "urgency": "high", "sentiment": "negative"},
    {"message": "I'm very disappointed with your service", "intent": "complaint", "urgency": "medium", "sentiment": "negative"},
    {"message": "The application crashes constantly", "intent": "complaint", "urgency": "high", "sentiment": "negative"},
    {"message": "Your support team is unhelpful", "intent": "complaint", "urgency": "medium", "sentiment": "negative"},
    {"message": "This is the worst experience I've ever had", "intent": "complaint", "urgency": "medium", "sentiment": "negative"},
    {"message": "Nothing works as advertised", "intent": "complaint", "urgency": "high", "sentiment": "negative"},
    {"message": "I'm frustrated with all these bugs", "intent": "complaint", "urgency": "medium", "sentiment": "negative"},
    {"message": "Your product is completely unreliable", "intent": "complaint", "urgency": "high", "sentiment": "negative"},
    {"message": "I want to file an official complaint", "intent": "complaint", "urgency": "medium", "sentiment": "negative"},
    {"message": "This is completely unacceptable behavior", "intent": "complaint", "urgency": "high", "sentiment": "negative"},
    {"message": "The system is down again, this is ridiculous", "intent": "complaint", "urgency": "high", "sentiment": "negative"},
    {"message": "I've been waiting for hours with no response", "intent": "complaint", "urgency": "high", "sentiment": "negative"},
    {"message": "Your latest update broke everything", "intent": "complaint", "urgency": "high", "sentiment": "negative"},
    {"message": "This error keeps happening and it's annoying", "intent": "complaint", "urgency": "medium", "sentiment": "negative"},
    {"message": "I'm tired of these constant issues", "intent": "complaint", "urgency": "medium", "sentiment": "negative"},
    
    # Service request examples (requests for help or services)
    {"message": "I need help setting up my account", "intent": "service_request", "urgency": "medium", "sentiment": "neutral"},
    {"message": "Can you help me configure this feature?", "intent": "service_request", "urgency": "medium", "sentiment": "neutral"},
    {"message": "I'd like to request a new feature", "intent": "service_request", "urgency": "low", "sentiment": "neutral"},
    {"message": "Please help me troubleshoot this issue", "intent": "service_request", "urgency": "medium", "sentiment": "neutral"},
    {"message": "I need assistance with the integration", "intent": "service_request", "urgency": "medium", "sentiment": "neutral"},
    {"message": "Can you provide training materials?", "intent": "service_request", "urgency": "low", "sentiment": "neutral"},
    {"message": "I want to upgrade my plan", "intent": "service_request", "urgency": "low", "sentiment": "positive"},
    {"message": "Please help me recover my lost data", "intent": "service_request", "urgency": "high", "sentiment": "neutral"},
    {"message": "I need technical support immediately", "intent": "service_request", "urgency": "high", "sentiment": "neutral"},
    {"message": "Can you schedule a demo for our team?", "intent": "service_request", "urgency": "low", "sentiment": "positive"},
    {"message": "I require urgent assistance with this problem", "intent": "service_request", "urgency": "high", "sentiment": "neutral"},
    {"message": "Could you help me migrate my data?", "intent": "service_request", "urgency": "medium", "sentiment": "neutral"},
    {"message": "I need someone to walk me through the setup", "intent": "service_request", "urgency": "medium", "sentiment": "neutral"},
    {"message": "Please provide me with custom integration support", "intent": "service_request", "urgency": "medium", "sentiment": "neutral"},
    {"message": "I want to request additional storage space", "intent": "service_request", "urgency": "low", "sentiment": "neutral"},
    
    # Mixed sentiment examples
    {"message": "I love your product but this bug is frustrating", "intent": "complaint", "urgency": "medium", "sentiment": "negative"},
    {"message": "Thanks for the great service, can you help with one more thing?", "intent": "service_request", "urgency": "low", "sentiment": "positive"},
    {"message": "Your support team is amazing, I just have a quick question", "intent": "query", "urgency": "low", "sentiment": "positive"},
    {"message": "I'm happy with most features but this one doesn't work", "intent": "complaint", "urgency": "medium", "sentiment": "negative"},
    {"message": "Excellent platform! How do I access advanced features?", "intent": "query", "urgency": "low", "sentiment": "positive"},
    
    # Edge cases and complex examples
    {"message": "Is there a way to automatically backup my data?", "intent": "query", "urgency": "low", "sentiment": "neutral"},
    {"message": "The system seems slow today, is everything okay?", "intent": "query", "urgency": "medium", "sentiment": "neutral"},
    {"message": "I accidentally deleted something important, help!", "intent": "service_request", "urgency": "high", "sentiment": "neutral"},
    {"message": "This used to work fine, now it's broken after the update", "intent": "complaint", "urgency": "medium", "sentiment": "negative"},
    {"message": "Can you add a feature for bulk operations?", "intent": "service_request", "urgency": "low", "sentiment": "neutral"},
    {"message": "The mobile app keeps logging me out", "intent": "complaint", "urgency": "medium", "sentiment": "negative"},
    {"message": "How do I export my data in CSV format?", "intent": "query", "urgency": "low", "sentiment": "neutral"},
    {"message": "I'm getting timeout errors when uploading files", "intent": "complaint", "urgency": "medium", "sentiment": "negative"},
    {"message": "Please whitelist my IP for API access", "intent": "service_request", "urgency": "medium", "sentiment": "neutral"},
    {"message": "What's the maximum file size I can upload?", "intent": "query", "urgency": "low", "sentiment": "neutral"},
    {"message": "The dashboard loads very slowly, can this be fixed?", "intent": "complaint", "urgency": "medium", "sentiment": "neutral"},
    {"message": "I need help customizing the email notifications", "intent": "service_request", "urgency": "low", "sentiment": "neutral"}
]


def get_test_cases():
    """Return the complete test dataset"""
    return TEST_CASES


def get_test_cases_by_intent(intent_type: str):
    """Get test cases filtered by intent type"""
    return [case for case in TEST_CASES if case['intent'] == intent_type]


def get_test_cases_by_urgency(urgency_level: str):
    """Get test cases filtered by urgency level"""
    return [case for case in TEST_CASES if case['urgency'] == urgency_level]


def get_test_cases_by_sentiment(sentiment_type: str):
    """Get test cases filtered by sentiment type"""
    return [case for case in TEST_CASES if case['sentiment'] == sentiment_type]


def print_dataset_stats():
    """Print statistics about the test dataset"""
    total = len(TEST_CASES)
    
    # Count by intent
    intents = {}
    urgencies = {}
    sentiments = {}
    
    for case in TEST_CASES:
        intents[case['intent']] = intents.get(case['intent'], 0) + 1
        urgencies[case['urgency']] = urgencies.get(case['urgency'], 0) + 1
        sentiments[case['sentiment']] = sentiments.get(case['sentiment'], 0) + 1
    
    print(f"Total test cases: {total}")
    print(f"Intent distribution: {intents}")
    print(f"Urgency distribution: {urgencies}")
    print(f"Sentiment distribution: {sentiments}")


if __name__ == "__main__":
    print_dataset_stats()