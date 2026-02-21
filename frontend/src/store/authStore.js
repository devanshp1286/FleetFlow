import { create } from 'zustand';
import { authAPI } from '../api/client';

const useAuthStore = create((set) => ({
  user: null,
  loading: false,
  error: null,

  login: async (username, password) => {
    set({ loading: true, error: null });
    try {
      const { data } = await authAPI.login({ username, password });
      localStorage.setItem('access_token',  data.data.access_token);
      localStorage.setItem('refresh_token', data.data.refresh_token);
      set({ user: data.data.user, loading: false });
      return { ok: true };
    } catch (err) {
      const msg = err.response?.data?.message || 'Login failed.';
      set({ error: msg, loading: false });
      return { ok: false, message: msg };
    }
  },

  register: async (body) => {
    set({ loading: true, error: null });
    try {
      const { data } = await authAPI.register(body);
      localStorage.setItem('access_token',  data.data.access_token);
      localStorage.setItem('refresh_token', data.data.refresh_token);
      set({ user: data.data.user, loading: false });
      return { ok: true };
    } catch (err) {
      const msg = err.response?.data?.message || 'Registration failed.';
      set({ error: msg, loading: false });
      return { ok: false, message: msg };
    }
  },

  logout: () => {
    localStorage.clear();
    set({ user: null });
  },

  hydrateUser: async () => {
    const token = localStorage.getItem('access_token');
    if (!token) return;
    try {
      const { data } = await authAPI.me();
      set({ user: data.data });
    } catch {
      localStorage.clear();
    }
  },
}));

export default useAuthStore;
