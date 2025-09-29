import ApiClient from './ApiClient';

class SessionAPI extends ApiClient {
  constructor() {
    super('session', { accountScoped: true });
  }

  start(params = {}) {
    return axios.post(`${this.apiVersion}/session/start`, params);
  }

  end(sessionId, params = {}) {
    return axios.post(`${this.apiVersion}/session/end`, {
      session_id: sessionId,
      ...params,
    });
  }

  getHistory(sessionId) {
    return axios.get(`${this.apiVersion}/session/history`, {
      params: { session_id: sessionId },
    });
  }

  clear(sessionId) {
    return axios.post(`${this.apiVersion}/session/clear`, {
      session_id: sessionId,
    });
  }
}

export default new SessionAPI();