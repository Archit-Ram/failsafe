import axios from "axios";

const baseURL =
  (import.meta.env.VITE_API_BASE as string | undefined) ?? "/api";

export const api = axios.create({ baseURL });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("failsafe_token");
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (resp) => resp,
  (error) => {
    if (error?.response?.status === 401) {
      localStorage.removeItem("failsafe_token");
      localStorage.removeItem("failsafe_user");
    }
    return Promise.reject(error);
  }
);
