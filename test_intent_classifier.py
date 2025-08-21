"""
Test script for intent classifier validation
Run this to test the accuracy of the intent classification system
"""

import sys
import os

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ai.intent_classifier import IntentClassifier
from ai.test_dataset import get_test_cases, print_dataset_stats

def run_classifier_tests():
    """Run comprehensive tests on the intent classifier"""
    print("=== EchoPilot Intent Classifier Test ===\n")
    
    # Print dataset statistics
    print("Test Dataset Statistics:")
    print_dataset_stats()
    print()
    
    # Initialize classifier
    print("Initializing Intent Classifier...")
    classifier = IntentClassifier()
    print()
    
    # Get test cases
    test_cases = get_test_cases()
    
    # Run accuracy test
    print(f"Running accuracy test on {len(test_cases)} test cases...")
    accuracy = classifier.get_test_accuracy(test_cases)
    print(f"Overall Accuracy: {accuracy:.2%}")
    
    # Target accuracy from implementation plan is >80%
    if accuracy >= 0.8:
        print("✅ PASSED: Accuracy meets the >80% target")
    else:
        print("❌ FAILED: Accuracy below 80% target")
    
    print()
    
    # Test individual predictions on sample cases
    print("=== Sample Predictions ===")
    sample_cases = [
        "I need help setting up my account",
        "This feature is completely broken!",
        "What are your business hours?",
        "I'm frustrated with these bugs",
        "Can you schedule a demo?",
        "How do I reset my password?"
    ]
    
    for message in sample_cases:
        analysis = classifier.analyze_message(message)
        print(f"Message: '{message}'")
        print(f"  Intent: {analysis.intent.value}")
        print(f"  Urgency: {analysis.urgency.value}")
        print(f"  Sentiment: {analysis.sentiment.value}")
        print(f"  Confidence: {analysis.confidence:.2f}")
        print()

if __name__ == "__main__":
    run_classifier_tests()