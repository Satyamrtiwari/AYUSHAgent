import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests if available
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Handle token refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/token/refresh/`, {
            refresh: refreshToken,
          });
          const { access } = response.data;
          localStorage.setItem('access_token', access);
          originalRequest.headers.Authorization = `Bearer ${access}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  register: (data) => api.post('/register/', data),
  login: (data) => api.post('/login/', data),
  googleLogin: (data) => api.post('/auth/google/', data),
  getMe: () => api.get('/me/'),
};

// Patient API
export const patientAPI = {
  list: () => api.get('/patients/'),
  create: (data) => api.post('/patients/', data),
  get: (id) => api.get(`/patients/${id}/`),
  update: (id, data) => api.put(`/patients/${id}/`, data),
  delete: (id) => api.delete(`/patients/${id}/`),
};

// Diagnosis API
export const diagnosisAPI = {
  list: () => api.get('/diagnoses/'),
  create: (data) => api.post('/diagnoses/', data),
  get: (id) => api.get(`/diagnoses/${id}/`),
  update: (id, data) => api.put(`/diagnoses/${id}/`, data),
  partialUpdate: (id, data) => api.patch(`/diagnoses/${id}/`, data),
  delete: (id) => api.delete(`/diagnoses/${id}/`),
};

// Pipeline API
export const pipelineAPI = {
  run: (data) => api.post('/run_pipeline/', data),
};

export default api;

