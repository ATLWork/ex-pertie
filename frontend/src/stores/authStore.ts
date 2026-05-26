import { create } from 'zustand'
import apiClient from '@/api/client'
import { userStore } from '@/services/asso'
import { isAnonymousEnabled, ANONYMOUS_USER } from '@/services/asso/config'

interface User {
  id: number
  username: string
  email: string
  created_at: string
  realName?: string
  userId?: string
}

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  isAnonymous: boolean
  login: () => Promise<void>
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
  isAnonymous: false,

  login: async () => {
    // Anonymous mode - no login needed
    if (isAnonymousEnabled()) {
      set({ user: ANONYMOUS_USER as User, isAuthenticated: true, isAnonymous: true })
      return
    }

    // ASSO login is handled in login page directly
    // This method is kept for compatibility but expects SSO to have set assoToken
    const assoToken = userStore.getToken()
    if (!assoToken) {
      throw new Error('No ASSO token available')
    }

    // Call backend to validate assoToken and get JWT
    const response = await apiClient.post('/auth/asso/callback', { assoToken })
    const { access_token } = response.data.data
    localStorage.setItem('token', access_token)

    // Get user info from ASSO store
    const assoUserInfo = userStore.userInfo

    set({
      user: {
        id: parseInt(assoUserInfo.userId || '0') || 0,
        username: assoUserInfo.userName || assoUserInfo.realName || '',
        email: assoUserInfo.email || '',
        created_at: '',
        realName: assoUserInfo.realName,
        userId: assoUserInfo.userId,
      },
      isAuthenticated: true,
      isAnonymous: false,
    })
  },

  register: async (username: string, email: string, password: string) => {
    await apiClient.post('/auth/register', { username, email, password })
  },

  logout: () => {
    localStorage.removeItem('token')
    localStorage.removeItem('anonymous_mode')
    userStore.clear()
    set({ user: null, isAuthenticated: false, isAnonymous: false })
  },

  checkAuth: async () => {
    // Anonymous mode - set anonymous user
    if (isAnonymousEnabled()) {
      set({ user: ANONYMOUS_USER as User, isAuthenticated: true, isLoading: false, isAnonymous: true })
      return
    }

    const token = localStorage.getItem('token')
    const assoToken = userStore.getToken()

    if (!token && !assoToken) {
      set({ isLoading: false, isAuthenticated: false, isAnonymous: false })
      return
    }

    try {
      // If we have JWT token, validate it with backend
      if (token) {
        const response = await apiClient.get('/auth/me')
        set({ user: response.data.data, isAuthenticated: true, isLoading: false, isAnonymous: false })
      } else if (assoToken) {
        // If only assoToken, need to get JWT first
        const response = await apiClient.post('/auth/asso/callback', { assoToken })
        const { access_token } = response.data.data
        localStorage.setItem('token', access_token)

        const userResponse = await apiClient.get('/auth/me')
        set({ user: userResponse.data.data, isAuthenticated: true, isLoading: false, isAnonymous: false })
      }
    } catch {
      localStorage.removeItem('token')
      set({ user: null, isAuthenticated: false, isLoading: false, isAnonymous: false })
    }
  },

  updateProfile: async (data: Partial<User>) => {
    const response = await apiClient.put('/auth/me', data)
    set({ user: response.data.data })
  },

  updatePassword: async (currentPassword: string, newPassword: string) => {
    await apiClient.put('/auth/me/password', { current_password: currentPassword, new_password: newPassword })
  },
}))