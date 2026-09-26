import { create } from 'zustand'
import { authAPI } from '../services/api'

export const PENDING_VERIFICATION_EMAIL_KEY = 'pending_verification_email'

const useAuthStore = create((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,

  init: async () => {
    const token = localStorage.getItem('access_token')
    if (!token) { set({ isLoading: false }); return }
    try {
      const { data } = await authAPI.me()
      set({ user: data, isAuthenticated: true, isLoading: false })
    } catch {
      localStorage.clear()
      set({ isLoading: false })
    }
  },

  login: async (email, password) => {
    const { data } = await authAPI.login({ email, password })
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    set({ user: data.user, isAuthenticated: true })
    return data
  },

  signup: async (formData) => {
    const { data } = await authAPI.signup(formData)
    sessionStorage.setItem(PENDING_VERIFICATION_EMAIL_KEY, data.user.email)
    set({ user: data.user, isAuthenticated: false })
    return data
  },

  setAuthenticatedUser: (data) => {
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    sessionStorage.removeItem(PENDING_VERIFICATION_EMAIL_KEY)
    set({ user: data.user, isAuthenticated: true })
  },

  // Update user in store after profile edit
  setUser: (user) => set({ user }),

  logout: () => {
    localStorage.clear()
    sessionStorage.removeItem(PENDING_VERIFICATION_EMAIL_KEY)
    set({ user: null, isAuthenticated: false })
    window.location.href = '/login'
  },
}))

export default useAuthStore