import axios from 'axios';

const API_BASE_URL =
  (typeof process !== 'undefined' && process.env.REACT_APP_API_URL) ||
  'https://scraplink-yz18.onrender.com'; // Or your Render URL

const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
});

axiosInstance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken');
    if (token) config.headers.Authorization = `Bearer ${token}`;

    if (config.data instanceof FormData) {
      delete config.headers['Content-Type'];
    } else if (!config.headers['Content-Type']) {
      config.headers['Content-Type'] = 'application/json';
    }
    return config;
  },
  (error) => Promise.reject(error)
);

axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    // Only clear the token on actual 401 Unauthorized
    if (error.response?.status === 401) {
      localStorage.removeItem('accessToken');
      // REMOVED hard redirect: window.location.href = '/login';
      // Redux/RoleRoute will handle the redirect naturally.
    }
    return Promise.reject(error);
  }
);

export default axiosInstance;