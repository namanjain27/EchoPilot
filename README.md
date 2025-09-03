# EchoPilot
Customer Success Copilot - an angentic AI RAG that does intent classification, autonomous decision making and tool calling 
<div style="position: relative; padding-bottom: 56.25%; height: 0;"><iframe src="https://www.loom.com/embed/52d3f6b3a6ac48318bb19dfad2ddfcff?sid=7f6c8b12-b8cd-4287-a79f-c3ac76a6ac77" frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe></div>
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
