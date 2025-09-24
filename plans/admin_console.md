# Admin Console - Multi-tenant RBAC Implementation Plan

## Goal:
1. We want this complete service to act as a SaaS. So our client will receive a unique tenant-id. The docs in our vector DB should have meta-data filter for tenant-id so that each client's chat accesses those docs only.

2. Moreover we will provide role based access control (RBAC) through our admin console. so while ingesting any file into the knowledge base, the client will be able to select the type of users who can access that doc. Type of users can be: {customer, vendor, associate, leadership, hr}. Therefore, while accessing an AI response, the user type will be checked and those docs can only be retrieved.

3. we are already doing session management so every chat session remains independent of one another is ensured.

4. there will be a database to store details for tenants and their access roles. To be planned in future.

for now.
we need to incorporate changes for:
1. creating new tenant-id
2. new meta-data filters for tenant-id and access role
3. on starting a new chat session - the above meta-data filtering should be used to fetch results.

## Implementation Plan

### Phase 1: Core Infrastructure Changes

#### 1. Metadata Schema Enhancement
**Location: `data_ingestion.py`**
- Extend `create_enhanced_metadata()` function to include:
  - `tenant_id`: Unique identifier for each tenant
  - `access_roles`: List of roles that can access the document
  - `document_visibility`: Public/Private/Restricted classification

#### 2. API Request Models Update
**Location: `api/models/requests.py`**
- Add new Pydantic models:
  - `TenantRequest`: Base class with tenant_id and user_role
  - `ChatRequestWithTenant`: Extends ChatRequest with tenant context
  - `KBUploadRequestWithTenant`: Extends KBUploadRequest with tenant and role selection
- Update existing models to inherit from tenant-aware base classes

#### 3. API Response Models Update
**Location: `api/models/responses.py`**
- Add tenant-aware response models:
  - `TenantAwareResponse`: Base response with tenant validation info
  - Update existing responses to include tenant context

### Phase 2: Data Ingestion Layer Modifications

#### 4. Enhanced Data Ingestion
**Location: `data_ingestion.py`**
- Modify `ingest_file_with_feedback()` to accept tenant_id and access_roles
- Update all extraction functions (`extract_pdf`, `extract_docx`, `extract_txt`) to include tenant metadata
- Add validation for tenant_id format and role permissions

#### 5. Vector Store Service Enhancement
**Location: `services.py`**
- Create tenant-aware vector store initialization
- Add metadata filtering capabilities for retrieval operations
- Implement tenant isolation at the collection level (optional future enhancement)

### Phase 3: Retrieval System Modifications

#### 6. Tenant-Aware Retrieval
**Location: `echo.py`**
- Modify `get_tools()` function to create tenant-aware retriever
- Update `retriever_tool()` to accept and use tenant context
- Implement metadata filtering in retrieval operations
- Add role-based document access validation

#### 7. Agent Context Enhancement
**Location: `echo_ui.py`**
- Modify `process_user_message()` to accept tenant_id and user_role
- Update agent initialization to handle tenant context
- Implement tenant validation before processing queries

### Phase 4: API Layer Integration

#### 8. Knowledge Base API Updates
**Location: `api/routes/knowledge_base.py`**
- Add tenant_id parameter to file upload endpoint
- Include role selection in upload process
- Implement tenant validation middleware
- Add metadata filtering for KB status queries

#### 9. Chat API Updates
**Location: `api/routes/chat.py`**
- Modify chat endpoints to accept tenant context
- Implement tenant validation before processing
- Add role-based filtering to retrieval operations

#### 10. Session Management Updates
**Location: `api/routes/session.py`**
- Add tenant context to session initialization
- Implement tenant-scoped session management
- Ensure session isolation across tenants

### Phase 5: Database Schema (Future Implementation)

#### 11. Tenant Management Database
- Design tenant table with columns:
  - `tenant_id` (UUID, Primary Key)
  - `tenant_name` (String)
  - `created_at` (Timestamp)
  - `is_active` (Boolean)
- Design user_roles table with columns:
  - `id` (Primary Key)
  - `tenant_id` (Foreign Key)
  - `user_id` (String)
  - `role` (Enum: customer, vendor, associate, leadership, hr)
  - `is_active` (Boolean)

### Implementation Order:

1. **Start with data_ingestion.py**: Add tenant metadata support
2. **Update API models**: Add tenant-aware request/response models
3. **Modify services.py**: Implement filtering capabilities
4. **Update echo.py**: Add tenant context to retrieval
5. **Modify echo_ui.py**: Add tenant processing support
6. **Update API routes**: Integrate tenant validation and filtering
7. **Test tenant isolation**: Ensure proper data segregation

### Key Functions to Modify:

#### `data_ingestion.py`:
- `create_enhanced_metadata(tenant_id, access_roles)`
- `ingest_file_with_feedback(file_path, tenant_id, access_roles)`
- `ingest_file_to_vectordb(file_paths, tenant_id, access_roles)`

#### `services.py`:
- Add `create_tenant_aware_retriever(tenant_id, user_role)`
- Add metadata filtering to vector store operations

#### `echo.py`:
- `get_tools(tenant_id, user_role)`
- Modify `retriever_tool()` to include tenant filtering

#### `echo_ui.py`:
- `process_user_message(message, tenant_id, user_role, processed_files)`
- `initialize_agent(tenant_id, user_role)`

#### API Routes:
- All endpoints to include tenant validation
- Add tenant context to request processing
- Implement role-based access control

### Testing Strategy:
1. Test tenant isolation in vector store
2. Verify role-based document access
3. Ensure cross-tenant data protection
4. Validate session isolation
5. Test API endpoint security

This implementation will transform the current single-tenant system into a fully multi-tenant SaaS platform with robust role-based access control. 