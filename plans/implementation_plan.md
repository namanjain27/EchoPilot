# EchoPilot Implementation Plan

## Overview
This plan outlines the phased implementation of EchoPilot, a customer success copilot app that automates support tasks for both internal associates and customers using RAG with intent analysis and tool calling.

## Phase 1: Core Foundation (Weeks 1-3)
**Goal**: Establish basic functionality and validate core AI capabilities

### 1.1 Project Structure Setup
- Set up modular Python project structure
- Initialize core modules: `intent_classifier`, `rag_engine`, `ticket_manager`, `auth_handler`
- Configure environment and dependencies (LangChain, Streamlit, ChromaDB, Gemini)

### 1.2 Basic Authentication & Role Management
- Implement simple role selection in Streamlit sidebar (Associate/Customer)
- Basic session state management for user roles
- Access control for different knowledge bases

### 1.3 Intent Classification System
- Develop intent classifier for: Query, Complaint, Service Request
- Add urgency detection (High/Medium/Low)
- Basic sentiment analysis (Positive/Negative/Neutral)
- Test with 50+ sample queries for accuracy validation

### 1.4 Data Persistence Layer
- Implement SQLite database for basic persistence
- Schema design for:
  - Chat sessions
  - Ticket data
  - User interactions
- Basic CRUD operations

## Phase 2: RAG & Knowledge Management (Weeks 4-5)
**Goal**: Implement knowledge retrieval and response generation

### 2.1 Knowledge Base Setup
- Initialize ChromaDB cloud integration
- Setup embedding model (sentence-transformers/all-MiniLM-L6-v2)
- Create knowledge base structure:
  - Internal KB (financial data, team structure, patents) - Associate only
  - General KB (services, FAQs, troubleshooting, T&Cs) - Both roles

### 2.2 RAG Pipeline Implementation
- Document ingestion and embedding pipeline
- Context-aware retrieval system
- Response generation using Gemini 2.5 Flash
- Context window management for multi-turn conversations

### 2.3 Conversation Memory
- Streamlit session state for conversation context
- Chat history storage and retrieval
- Session summary generation for closed chats

## Phase 3: Tool Integration (Weeks 6-7)
**Goal**: Implement external tool calling and ticket management

### 3.1 Jira Integration
- Jira API integration for ticket creation
- Tool calling framework implementation
- Ticket types:
  - Complaint tickets (Customer)
  - Service request tickets (Customer)
  - Feature request tickets (Associate)

### 3.2 Complaint Validation System
- Validity checking against general knowledge base
- Automated reasoning for invalid complaints
- Ticket creation flow for valid complaints

### 3.3 Ticket Management
- Unique ticket ID generation
- Ticket status tracking
- Reference system for customers

## Phase 4: User Interface & Experience (Week 8)
**Goal**: Enhance user experience and interface

### 4.1 Streamlit Frontend Enhancement
- Text + image input processing
- Role-based UI customization
- Chat interface improvements
- Conversation history display

### 4.2 Error Handling & Validation
- Comprehensive error handling for API failures
- Input validation and sanitization
- User-friendly error messages

### 4.3 Basic Logging & Monitoring
- Interaction logging for analysis
- Performance metrics tracking
- Basic conversation export functionality

## Phase 5: Testing & Validation (Week 9)
**Goal**: Comprehensive testing and validation

### 5.1 Core Functionality Testing
- Intent classification accuracy (target: >80%)
- RAG response quality validation
- Jira integration testing
- Role-based access testing

### 5.2 Performance Testing
- Response time optimization (target: <5 seconds)
- Knowledge retrieval relevance evaluation
- Successful ticket creation rate testing

### 5.3 User Experience Testing
- End-to-end workflow testing
- Associate vs Customer mode validation
- Conversation context maintenance testing

## Technical Architecture

### Core Components
```
src/
├── auth/
│   ├── role_manager.py
│   └── session_handler.py
├── ai/
│   ├── intent_classifier.py
│   ├── rag_engine.py
│   └── gemini_client.py
├── data/
│   ├── database.py
│   ├── knowledge_base.py
│   └── embeddings.py
├── integrations/
│   ├── jira_client.py
│   └── ticket_manager.py
├── ui/
│   ├── streamlit_app.py
│   └── components/
└── utils/
    ├── logging.py
    └── validators.py
```

### Key Technologies
- **Frontend**: Streamlit
- **AI/ML**: Google Gemini 2.5 Flash, LangChain
- **Vector DB**: ChromaDB (cloud)
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2
- **Database**: SQLite (for prototype)
- **Integration**: Jira API

## Success Metrics

### Phase 1 Completion Criteria
- ✅ Role-based authentication working
- ✅ Intent classification with >80% accuracy
- ✅ Basic data persistence functional
- ✅ Session management operational

### Final Prototype Validation
- ✅ Text + image input processing
- ✅ Intent classification (query/complaint/service)
- ✅ RAG-based responses from knowledge base
- ✅ Jira ticket creation for complaints
- ✅ Associate vs Customer mode differentiation
- ✅ Conversation context maintenance
- ✅ Basic ticket ID generation and tracking

## Risk Mitigation

### Technical Risks
- **Gemini API reliability**: Implement fallback mechanisms
- **ChromaDB performance**: Local fallback option
- **Jira integration**: Mock service for testing

### Scope Risks
- **Feature creep**: Strict adherence to prototype scope
- **Over-engineering**: Follow CLAUDE.md principles for simplicity

## Next Steps After Prototype
1. User feedback collection and analysis
2. Performance optimization based on real usage
3. Security enhancements for production
4. Scalability improvements
5. Advanced analytics and reporting

## Development Guidelines
Following CLAUDE.md principles:
- Use `snake_case` naming conventions
- Keep functions modular and focused
- Prioritize clarity over cleverness
- Add comments explaining WHY, not WHAT
- Separate utility functions into appropriately named modules