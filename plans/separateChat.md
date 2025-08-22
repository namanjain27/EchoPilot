# Separate Chat Modes Implementation Plan

## Current Issue Analysis

The EchoPilot application currently has a single shared chat history across Associate and Customer modes. When users switch between roles, they can see messages from the previous role, which compromises the separation of concerns and privacy between different user types.

### Current Implementation Problems:
- Single `chat_history` stored in `SessionHandler` without role separation
- `get_chat_history()` and `add_message()` methods don't consider user roles
- Role switching maintains the same conversation context
- Clear chat button clears all history regardless of role

## Implementation Plan

### Phase 1: Backend Session Handler Updates 

#### 1.1 Update SessionHandler Class (`src/auth/session_handler.py`)
- **Modify chat storage structure**: Change from single list to role-based dictionary
  ```python
  # Current: self.chat_history = []
  # New: self.chat_histories = {"associate": [], "customer": []}
  ```

- **Update method signatures**: Modify chat methods to accept optional role parameter
  ```python
  def get_chat_history(self, role: UserRole = None) -> List[Dict]
  def add_message(self, message: Dict, role: UserRole = None) 
  def clear_chat_history(self, role: UserRole = None)
  ```

- **Add role-specific methods**: Create convenience methods for role-specific operations
  ```python
  def get_current_role_chat_history() -> List[Dict]
  def add_message_for_current_role(message: Dict)
  def clear_current_role_chat_history()
  ```

### Phase 2: UI Layer Updates 

#### 2.1 Update Streamlit App (`src/ui/streamlit_app.py`)

- **Modify chat display logic**: Update chat history retrieval to use current role
  ```python
  # Line ~149: chat_history = st.session_state.session_handler.get_chat_history()
  # Change to: chat_history = st.session_state.session_handler.get_current_role_chat_history()
  ```

- **Update message handling**: Ensure messages are added to correct role's chat
  ```python
  # Line ~176 & ~207: st.session_state.session_handler.add_message(message)
  # Change to: st.session_state.session_handler.add_message_for_current_role(message)
  ```

- **Update clear chat button**: Modify to clear only current role's history
  ```python
  # Line ~123: st.session_state.session_handler.clear_chat_history()
  # Change to: st.session_state.session_handler.clear_current_role_chat_history()
  ```

#### 2.2 Add Role Transition Handling

- **Role switch detection**: Add logic to detect when user switches roles
  ```python
  # After role update (line ~102), trigger chat history switch
  if selected_role != current_role:
      # Switch to role-specific chat history
      # Update UI to show role-specific message count
  ```

- **Update chat statistics**: Show role-specific message counts
  ```python
  # Line ~128: Show current role's message count only
  current_role_history = st.session_state.session_handler.get_current_role_chat_history()
  st.caption(f"Messages in {current_role.value} mode: {len(current_role_history)}")
  ```

### Phase 3: Enhanced Features 

#### 3.1 Role-Specific Chat Context
- **Separate RAG context**: Ensure RAG responses use only current role's chat history
  ```python
  # Line ~186: chat_history = st.session_state.session_handler.get_chat_history()
  # Change to: chat_history = st.session_state.session_handler.get_current_role_chat_history()
  ```

#### 3.2 Advanced Clear Options (Optional Enhancement)
- **Add "Clear All Chats" option**: For complete reset across both roles
- **Add confirmation dialogs**: Prevent accidental chat clearing

## Implementation Priority

### High Priority (Core Functionality):
1. SessionHandler chat storage modification
2. Streamlit UI chat display updates  
3. Role-specific message handling
4. Clear chat button role separation

### Medium Priority (Enhanced UX):
1. Chat statistics per role
2. Role transition smoothness

### Low Priority (Nice to Have):
1. Advanced clear options
2. Confirmation dialogs

## Technical Considerations

### Memory Management:
- Two separate chat histories will use more memory
- Consider implementing chat history limits per role
- Add cleanup mechanisms for old conversations

### Performance:
- Role-specific operations are lightweight (in-memory only)
- Consider caching strategies for frequent role switches

### Security:
- Ensure complete isolation between role-specific chats
- Validate role access in all chat operations
- Prevent cross-role data leakage

### Testing Strategy:
- Unit tests for SessionHandler role separation
- Integration tests for UI role switching
- Edge case testing (empty histories, role transitions)

## Success Criteria

1. **Complete Separation**: Associate and Customer chats are completely separate
2. **Persistence**: Each role's chat history persists when switching roles
3. **Independent Clearing**: Clear chat only affects current role's history
4. **Seamless UX**: Role switching is smooth without data loss
5. **Backward Compatibility**: Existing functionality remains intact

## Estimated Implementation Time

- **Phase 1**: 1-2 hours (Backend updates)
- **Phase 2**: 2-3 hours (UI updates) 
- **Phase 3**: 1 hour (Enhanced features)

**Total**: 4-6 hours of development time

## Files to Modify

### Core Files:
- `src/auth/session_handler.py` - Chat storage and management
- `src/ui/streamlit_app.py` - UI chat display and interaction

### Supporting Files:
- `plans/workdone.md` - Documentation updates

This implementation will provide complete chat separation between Associate and Customer modes while maintaining all existing functionality and ensuring a smooth user experience.