import axios from 'axios';
import { getGateway } from './constant';
import { userStore } from './store';
import { login } from './login';

const request = axios.create({
  baseURL: getGateway(),
  timeout: 15000,
  withCredentials: true,
});

request.interceptors.request.use((config) => {
  const token = userStore.getToken();
  if (token) {
    config.headers['assoToken'] = token;
  }
  return config;
});

request.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      userStore.clear();
      login().goToLogin();
    }
    return Promise.reject(error);
  }
);

export default request;