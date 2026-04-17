import axios from 'axios';

const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

if (import.meta.env.PROD && apiUrl && !apiUrl.startsWith('https://')) {
  console.warn(
    `[Voss CRM] VITE_API_URL does not use HTTPS: "${apiUrl}". ` +
    'This is insecure for production deployments.'
  );
}

const api = axios.create({
  baseURL: apiUrl,
});

function getToken(): string | null {
  return localStorage.getItem('token') || sessionStorage.getItem('token');
}

function setToken(token: string) {
  if (localStorage.getItem('rememberMe') === 'true') {
    localStorage.setItem('token', token);
  } else {
    sessionStorage.setItem('token', token);
  }
}

function clearToken() {
  localStorage.removeItem('token');
  localStorage.removeItem('rememberMe');
  sessionStorage.removeItem('token');
}

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let isRefreshing = false;
let refreshQueue: Array<{ resolve: (token: string) => void; reject: (err: unknown) => void }> = [];

function processQueue(token: string | null, error: unknown = null) {
  refreshQueue.forEach(({ resolve, reject }) => {
    if (token) resolve(token);
    else reject(error);
  });
  refreshQueue = [];
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      // Don't try to refresh the refresh call itself
      if (originalRequest.url?.includes('/api/auth/refresh')) {
        clearToken();
        window.location.href = '/login';
        return Promise.reject(error);
      }

      if (isRefreshing) {
        // Queue this request until the refresh completes
        return new Promise((resolve, reject) => {
          refreshQueue.push({
            resolve: (token: string) => {
              originalRequest.headers.Authorization = `Bearer ${token}`;
              resolve(api(originalRequest));
            },
            reject,
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const currentToken = getToken();
        const { data } = await axios.post(`${apiUrl}/api/auth/refresh`, null, {
          headers: { Authorization: `Bearer ${currentToken}` },
        });
        const newToken = data.access_token;
        setToken(newToken);
        processQueue(newToken);
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(null, refreshError);
        clearToken();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default api;
