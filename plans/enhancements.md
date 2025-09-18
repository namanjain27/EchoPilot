# Goal
we need to do code changes to ensure:
1. correct docs are pulled out from the RAG KB -> scoring
2. if the question is big and vague then we need to do query transformation to break the user query into multiple questions that go from general to advanced. This ensures that all necessary information is extracted from RAG and feed into LLM for final answer. -> new initial llm node 
3. final answer satisfies the user needs from the query -> reviewer agent
4. feedback for each answer
