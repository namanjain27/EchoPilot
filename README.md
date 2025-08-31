# EchoPilot
Customer Success Copilot - an angentic AI RAG that does intent classification, autonomous decision making and tool calling 

## Tech-Stack
python
langchain and langGraph
chromaDB
streamlit for UI

## Layers:
Data ingestion - data_ingestion.py
main graph and nodes decleration - echo.py
ticket creation - jira_tool.py
loading and saving chat history - chat_mgmt.py
embedding model and vector store service - services.py
multi-modal input processing - multiModalInputService.py

## Expectations:
1. user can ingest files to vector db that persists data locally
2. RAG framework with tool calling like data retrieval and ticket creation
3. internal analysis flow: intent analysis -> RAG -> relevant tool calling
4. chat memory is stored
5. user can add files like image and pdf in the user query