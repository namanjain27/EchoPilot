"""
Complaint validation system for EchoPilot
Validates complaints against knowledge base and provides automated reasoning
"""

import logging
from typing import Dict, Any, List, Tuple, Optional, TYPE_CHECKING
import re

if TYPE_CHECKING:
    from .rag_engine import RAGEngine
    
from .gemini_client import GeminiClient


class ComplaintValidator:
    """Validates complaints against knowledge base and provides reasoning"""
    
    def __init__(self, rag_engine: "RAGEngine", gemini_client: GeminiClient):
        self.rag_engine = rag_engine
        self.gemini_client = gemini_client
        self.logger = logging.getLogger(__name__)
        
        # Common valid complaint indicators
        self.valid_complaint_indicators = [
            "bug", "error", "broken", "not working", "issue", "problem",
            "failed", "crash", "slow", "delay", "unavailable", "down",
            "incorrect", "wrong", "missing", "lost", "billing", "charge",
            "overcharged", "unauthorized", "poor service", "rude", "unhelpful"
        ]
        
        # Common invalid complaint patterns (things covered by documentation)
        self.invalid_complaint_patterns = [
            "how to", "how do i", "what is", "where is", "when does",
            "tutorial", "guide", "help me", "show me", "explain"
        ]
    
    def validate_complaint(self, complaint_text: str, user_role: str = "customer") -> Dict[str, Any]:
        """
        Validate a complaint against knowledge base
        
        Args:
            complaint_text: The complaint text to validate
            user_role: User role for knowledge base access
            
        Returns:
            Validation result with is_valid flag and reasoning
        """
        try:
            # Step 1: Basic pattern analysis
            basic_validity = self._basic_validity_check(complaint_text)
            
            # Step 2: Search knowledge base for relevant information
            relevant_docs = self.rag_engine.retrieve_documents(complaint_text, user_role, limit=5)
            
            # Step 3: Use AI to analyze complaint validity
            ai_analysis = self._ai_validate_complaint(complaint_text, relevant_docs)
            
            # Step 4: Combine results
            final_result = self._combine_validation_results(basic_validity, ai_analysis, relevant_docs)
            
            self.logger.info(f"Complaint validation completed: {'Valid' if final_result['is_valid'] else 'Invalid'}")
            
            return final_result
            
        except Exception as e:
            self.logger.error(f"Error validating complaint: {str(e)}")
            return {
                "is_valid": True,  # Default to valid on error to avoid blocking legitimate complaints
                "confidence": 0.5,
                "reasoning": f"Validation error occurred: {str(e)}. Treating complaint as valid by default.",
                "validation_method": "error_fallback",
                "relevant_documents": []
            }
    
    def _basic_validity_check(self, complaint_text: str) -> Dict[str, Any]:
        """Perform basic pattern-based validity check"""
        complaint_lower = complaint_text.lower()
        
        # Check for valid complaint indicators
        valid_indicators_found = [
            indicator for indicator in self.valid_complaint_indicators 
            if indicator in complaint_lower
        ]
        
        # Check for invalid complaint patterns (questions/requests for help)
        invalid_patterns_found = [
            pattern for pattern in self.invalid_complaint_patterns 
            if pattern in complaint_lower
        ]
        
        # Basic scoring
        validity_score = len(valid_indicators_found) - len(invalid_patterns_found) * 0.5
        
        return {
            "is_valid": validity_score > 0,
            "confidence": min(max(validity_score / 3.0, 0.0), 1.0),
            "valid_indicators": valid_indicators_found,
            "invalid_patterns": invalid_patterns_found
        }
    
    def _ai_validate_complaint(self, complaint_text: str, relevant_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use AI to validate complaint against knowledge base"""
        try:
            # Prepare context from relevant documents
            context = self._prepare_validation_context(relevant_docs)
            
            validation_prompt = f"""
You are a customer service expert analyzing a complaint for validity. Your job is to determine if this is a legitimate complaint or if it's actually a question/request that is already addressed in our documentation.

COMPLAINT TO ANALYZE:
{complaint_text}

RELEVANT DOCUMENTATION:
{context}

ANALYSIS CRITERIA:
1. VALID COMPLAINT: Issues with service quality, billing problems, technical failures, poor customer service experiences, broken features, bugs, or legitimate grievances
2. INVALID COMPLAINT: Questions asking for help, tutorials, information that's already documented, or requests that aren't actually complaints

Respond with a JSON object containing:
- is_valid: boolean (true if legitimate complaint, false if it's a question/documented issue)
- confidence: float between 0.0 and 1.0
- reasoning: detailed explanation of why this is/isn't a valid complaint
- key_factors: list of key factors that influenced the decision

Example responses:
{{"is_valid": true, "confidence": 0.9, "reasoning": "This is a legitimate complaint about billing being incorrect, which is a service quality issue not addressed in documentation.", "key_factors": ["billing issue", "service quality problem"]}}

{{"is_valid": false, "confidence": 0.8, "reasoning": "This is asking how to reset password, which is clearly documented in our help section.", "key_factors": ["how-to question", "documented procedure"]}}
"""
            
            response = self.gemini_client.generate_response(validation_prompt, [])
            
            # Try to parse JSON response
            try:
                import json
                # Extract JSON from response if it contains other text
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    return {
                        "is_valid": result.get("is_valid", True),
                        "confidence": result.get("confidence", 0.5),
                        "reasoning": result.get("reasoning", "AI analysis completed"),
                        "key_factors": result.get("key_factors", [])
                    }
                else:
                    # Fallback parsing if no JSON found
                    is_valid = "valid" in response.lower() and "invalid" not in response.lower()
                    return {
                        "is_valid": is_valid,
                        "confidence": 0.6,
                        "reasoning": response[:500],
                        "key_factors": []
                    }
            except json.JSONDecodeError:
                # Fallback to text analysis
                is_valid = "not valid" not in response.lower() and "invalid" not in response.lower()
                return {
                    "is_valid": is_valid,
                    "confidence": 0.6,
                    "reasoning": response[:500],
                    "key_factors": []
                }
                
        except Exception as e:
            self.logger.error(f"Error in AI validation: {str(e)}")
            return {
                "is_valid": True,  # Default to valid on AI error
                "confidence": 0.5,
                "reasoning": f"AI validation failed: {str(e)}. Defaulting to valid.",
                "key_factors": []
            }
    
    def _prepare_validation_context(self, relevant_docs: List[Dict[str, Any]]) -> str:
        """Prepare context from relevant documents for validation"""
        if not relevant_docs:
            return "No relevant documentation found."
        
        context_parts = []
        for i, doc in enumerate(relevant_docs[:3], 1):  # Use top 3 documents
            content = doc.get("content", "")
            source = doc.get("metadata", {}).get("source", "Unknown")
            
            # Truncate content if too long
            if len(content) > 300:
                content = content[:300] + "..."
            
            context_parts.append(f"Document {i} (Source: {source}):\n{content}")
        
        return "\n\n".join(context_parts)
    
    def _combine_validation_results(self, basic_result: Dict[str, Any], ai_result: Dict[str, Any], 
                                   relevant_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine basic and AI validation results"""
        
        # Weight the results (AI gets more weight if confidence is high)
        ai_weight = ai_result["confidence"]
        basic_weight = 1 - ai_weight
        
        # Combine validity decisions
        if ai_result["confidence"] > 0.7:
            # High AI confidence - use AI decision
            final_validity = ai_result["is_valid"]
            final_confidence = ai_result["confidence"]
            validation_method = "ai_primary"
        elif basic_result["confidence"] > 0.7:
            # High basic confidence - use basic decision
            final_validity = basic_result["is_valid"]
            final_confidence = basic_result["confidence"]
            validation_method = "pattern_primary"
        else:
            # Low confidence from both - combine decisions (bias toward valid for edge cases)
            combined_score = (ai_result["is_valid"] * ai_weight + 
                             basic_result["is_valid"] * basic_weight)
            final_validity = combined_score > 0.4  # Slightly bias toward valid
            final_confidence = (ai_result["confidence"] + basic_result["confidence"]) / 2
            validation_method = "combined"
        
        # Compile reasoning
        reasoning_parts = []
        if basic_result.get("valid_indicators"):
            reasoning_parts.append(f"Found valid complaint indicators: {', '.join(basic_result['valid_indicators'])}")
        if basic_result.get("invalid_patterns"):
            reasoning_parts.append(f"Found question patterns: {', '.join(basic_result['invalid_patterns'])}")
        if ai_result.get("reasoning"):
            reasoning_parts.append(f"AI Analysis: {ai_result['reasoning']}")
        
        final_reasoning = ". ".join(reasoning_parts) if reasoning_parts else "Analysis completed."
        
        return {
            "is_valid": final_validity,
            "confidence": final_confidence,
            "reasoning": final_reasoning,
            "validation_method": validation_method,
            "basic_analysis": basic_result,
            "ai_analysis": ai_result,
            "relevant_documents": [
                {
                    "source": doc.get("metadata", {}).get("source", "Unknown"),
                    "content_preview": doc.get("content", "")[:150] + "..." if len(doc.get("content", "")) > 150 else doc.get("content", "")
                } for doc in relevant_docs[:3]
            ]
        }
    
    def generate_invalid_complaint_response(self, complaint_text: str, validation_result: Dict[str, Any]) -> str:
        """Generate a helpful response for invalid complaints (questions disguised as complaints)"""
        relevant_docs = validation_result.get("relevant_documents", [])
        
        if not relevant_docs:
            return ("I understand you're looking for help with this matter. While this appears to be a question rather than a complaint, "
                   "I'd be happy to help you find the information you need. Could you please rephrase your question so I can assist you better?")
        
        response = ("I see you're looking for assistance with this matter. Based on our documentation, I found some relevant information that might help:\n\n")
        
        for doc in relevant_docs[:2]:
            response += f"• {doc['content_preview']}\n"
        
        response += ("\nIf you're experiencing an actual problem or issue with our service, please let me know the specific details "
                    "of what's not working correctly, and I'll be happy to help resolve it.")
        
        return response