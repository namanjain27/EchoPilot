import { API } from 'widget/helpers/axios';

const sendChatMessageAPI = async (message, sessionId = null, files = null) => {
  const formData = new FormData();
  formData.append('message', message);

  if (sessionId) {
    formData.append('session_id', sessionId);
  }

  if (files && files.length > 0) {
    files.forEach(file => formData.append('files', file));
  }

  return API.post('/api/v1/chat', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

const sendChatMessageTenantAPI = async (message, tenantId, userRole, sessionId = null, files = null) => {
  const formData = new FormData();
  formData.append('message', message);
  formData.append('tenant_id', tenantId);
  formData.append('user_role', userRole);

  if (sessionId) {
    formData.append('session_id', sessionId);
  }

  if (files && files.length > 0) {
    files.forEach(file => formData.append('files', file));
  }

  return API.post('/api/v1/chat-tenant', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

const startSessionAPI = async (tenantId = null) => {
  const params = {};
  if (tenantId) params.tenant_id = tenantId;

  return API.post('/api/v1/session/start', params);
};

const endSessionAPI = async (sessionId, saveHistory = true) => {
  return API.post('/api/v1/session/end', {
    session_id: sessionId,
    save_history: saveHistory,
  });
};

const getSessionHistoryAPI = async (sessionId) => {
  return API.get('/api/v1/session/history', {
    params: { session_id: sessionId },
  });
};

const clearSessionAPI = async (sessionId) => {
  return API.post('/api/v1/session/clear', {
    session_id: sessionId,
  });
};

export {
  sendChatMessageAPI,
  sendChatMessageTenantAPI,
  startSessionAPI,
  endSessionAPI,
  getSessionHistoryAPI,
  clearSessionAPI,
};