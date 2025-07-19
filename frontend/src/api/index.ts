import axios from 'axios';
import { ElMessage } from 'element-plus';
import { useUserStore } from '@/stores/user';

// 创建 Axios 实例
const apiClient = axios.create({
  baseURL: 'http://127.0.0.1:8000/api', // 后端 API 的基础 URL
  timeout: 10000, // 请求超时时间
});

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    const userStore = useUserStore();
    if (userStore.token) {
      config.headers.Authorization = `Token ${userStore.token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    let message = '发生未知错误';
    if (error.response) {
      switch (error.response.status) {
        case 400:
          const errors = error.response.data;
          if (typeof errors === 'object' && errors !== null) {
            message = Object.values(errors).flat().join('; ');
          } else {
            message = '请求参数错误';
          }
          break;
        case 401:
          message = '认证失败，请重新登录';
          useUserStore().clearAuth();
          window.location.href = '/login';
          break;
        case 403:
          message = '您没有权限执行此操作';
          break;
        case 404:
          message = '请求的资源未找到';
          break;
        case 500:
          message = '服务器内部错误';
          break;
        default:
          message = `请求失败，状态码：${error.response.status}`;
      }
    } else if (error.request) {
      message = '无法连接到服务器，请检查您的网络';
    } else {
      message = error.message;
    }
    
    ElMessage({
      message: message,
      type: 'error',
      duration: 5 * 1000,
    });

    return Promise.reject(error);
  }
);

export default apiClient;
