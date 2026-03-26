import { create } from 'zustand';
import type { User } from './types.ts';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
}

interface ToastState {
  message: string;
  type: 'success' | 'error' | 'info';
  visible: boolean;
}

interface AppStore {
  auth: AuthState;
  toast: ToastState;
  login: (user: User) => void;
  logout: () => void;
  showToast: (message: string, type: 'success' | 'error' | 'info') => void;
  hideToast: () => void;
}

export const useStore = create<AppStore>((set) => ({
  auth: {
    user: null,
    isAuthenticated: false,
  },
  toast: {
    message: '',
    type: 'info',
    visible: false,
  },
  login: (user: User) =>
    set({ auth: { user, isAuthenticated: true } }),
  logout: () =>
    set({ auth: { user: null, isAuthenticated: false } }),
  showToast: (message: string, type: 'success' | 'error' | 'info') =>
    set({ toast: { message, type, visible: true } }),
  hideToast: () =>
    set((state) => ({ toast: { ...state.toast, visible: false } })),
}));
