import { create } from 'zustand'
import apiClient from '@/api/client'

interface User {
  id: number
  username: string
  email: string
  created_at: string
}

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (username: string, password: string) => Promise<void>
  register: (username: string, email: string, password: string) => Promise<void>
  logout: () => void
  checkAuth: () => Promise<void>
  updateProfile: (data: Partial<User>) => Promise<void>
  updatePassword: (currentPassword: string, newPassword: string) => Promise<void>
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,

  login: async (username: string, password: string) => {
    const response = await apiClient.post('/auth/login', { username, password })
    const { access_token } = response.data
    localStorage.setItem('token', access_token)
    const userResponse = await apiClient.get('/auth/me')
    set({ user: userResponse.data, isAuthenticated: true })
  },

  register: async (username: string, email: string, password: string) => {
    await apiClient.post('/auth/register', { username, email, password })
  },

  logout: () => {
    localStorage.removeItem('token')
    set({ user: null, isAuthenticated: false })
  },

  checkAuth: async () => {
    const token = localStorage.getItem('token')
    if (!token) {
      set({ isLoading: false, isAuthenticated: false })
      return
    }
    try {
      const response = await apiClient.get('/auth/me')
      set({ user: response.data, isAuthenticated: true, isLoading: false })
    } catch {
      localStorage.removeItem('token')
      set({ user: null, isAuthenticated: false, isLoading: false })
    }
  },

  updateProfile: async (data: Partial<User>) => {
    const response = await apiClient.put('/auth/me', data)
    set({ user: response.data })
  },

  updatePassword: async (currentPassword: string, newPassword: string) => {
    await apiClient.put('/auth/me/password', { current_password: currentPassword, new_password: newPassword })
  },
}))
