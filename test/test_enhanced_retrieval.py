#!/usr/bin/env python3
"""
Test script for enhanced retrieval with RAG scoring integration
Tests the multi-search functionality in echo.py
"""

import os
from pathlib import Path

def test_import_dependencies():
    """Test that all required dependencies can be imported"""
    try:
        print("Testing imports...")

        # Test RAG scoring import
        from rag_scoring import score_documents, RAGScoringService
        print("✓ RAG scoring service imported successfully")

        # Test echo module imports
        from echo import get_tools, create_agent
        print("✓ Echo module imported successfully")

        # Test that tools are created properly
        tools = get_tools()
        tool_names = [tool.name for tool in tools]
        print(f"✓ Tools available: {tool_names}")

        # Verify retriever_tool exists and has enhanced description
        retriever_tool = next((tool for tool in tools if tool.name == "retriever_tool"), None)
        if retriever_tool:
            print("✓ Enhanced retriever_tool found")
            print(f"  Description includes multi-search guidance: {'multiple times' in retriever_tool.description}")
        else:
            print("✗ retriever_tool not found")

        return True

    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_agent_creation():
    """Test that the agent can be created with enhanced functionality"""
    try:
        print("\\nTesting agent creation...")

        from echo import create_agent
        agent = create_agent()

        if agent:
            print("✓ Enhanced agent created successfully")
            return True
        else:
            print("✗ Agent creation failed")
            return False

    except Exception as e:
        print(f"✗ Agent creation error: {e}")
        return False

def test_system_prompt_enhancement():
    """Test that system prompt includes multi-search guidance"""
    try:
        print("\\nTesting system prompt enhancement...")

        # Read the echo.py file to verify system prompt content
        script_dir = Path(__file__).parent
        echo_file = script_dir / "echo.py"

        if echo_file.exists():
            with open(echo_file, 'r') as f:
                content = f.read()

            # Check for key multi-search guidance
            has_retrieval_strategy = "Retrieval Strategy" in content
            has_complex_example = "Complex Query" in content
            has_redundancy_warning = "AVOID redundant searches" in content

            print(f"✓ Retrieval Strategy section: {has_retrieval_strategy}")
            print(f"✓ Complex Query example: {has_complex_example}")
            print(f"✓ Redundancy warning: {has_redundancy_warning}")

            if has_retrieval_strategy and has_complex_example and has_redundancy_warning:
                print("✓ System prompt properly enhanced for multi-search")
                return True
            else:
                print("✗ System prompt missing some multi-search guidance")
                return False
        else:
            print("✗ echo.py file not found")
            return False

    except Exception as e:
        print(f"✗ System prompt test error: {e}")
        return False

def run_all_tests():
    """Run all tests and report results"""
    print("=== Enhanced Retrieval Implementation Test ===\\n")

    tests = [
        ("Import Dependencies", test_import_dependencies),
        ("Agent Creation", test_agent_creation),
        ("System Prompt Enhancement", test_system_prompt_enhancement),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\\n--- {test_name} ---")
        try:
            if test_func():
                passed += 1
                print(f"✓ {test_name} PASSED")
            else:
                print(f"✗ {test_name} FAILED")
        except Exception as e:
            print(f"✗ {test_name} ERROR: {e}")

    print(f"\\n=== Test Results: {passed}/{total} tests passed ===")

    if passed == total:
        print("\\n🎉 All tests passed! Enhanced retrieval implementation is ready.")
        print("\\nNext steps:")
        print("1. Test with actual queries to verify multi-search behavior")
        print("2. Monitor retrieval relevance scores in action")
        print("3. Validate that simple queries use single search")
        print("4. Verify complex queries trigger multiple targeted searches")
    else:
        print(f"\\n⚠️  {total - passed} tests failed. Please fix issues before proceeding.")

    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)