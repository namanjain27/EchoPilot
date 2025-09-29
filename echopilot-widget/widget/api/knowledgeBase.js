import ApiClient from './ApiClient';

class KnowledgeBaseAPI extends ApiClient {
  constructor() {
    super('knowledge-base', { accountScoped: true });
  }

  upload(files, params = {}) {
    const formData = new FormData();

    // Add files to form data
    if (Array.isArray(files)) {
      files.forEach(file => formData.append('files', file));
    } else {
      formData.append('files', files);
    }

    // Add additional parameters
    Object.keys(params).forEach(key => {
      formData.append(key, params[key]);
    });

    return axios.post(`${this.apiVersion}/knowledge-base/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }

  uploadTenant(files, tenantId, params = {}) {
    const formData = new FormData();

    // Add files to form data
    if (Array.isArray(files)) {
      files.forEach(file => formData.append('files', file));
    } else {
      formData.append('files', files);
    }

    // Add tenant context
    formData.append('tenant_id', tenantId);

    // Add additional parameters
    Object.keys(params).forEach(key => {
      formData.append(key, params[key]);
    });

    return axios.post(`${this.apiVersion}/knowledge-base/upload-tenant`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }
}

export default new KnowledgeBaseAPI();