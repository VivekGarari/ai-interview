import { create } from 'zustand'
import { authAPI } from '../services/api'

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
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    set({ user: data.user, isAuthenticated: true })
    return data
  },

  // Update user in store after profile edit
  setUser: (user) => set({ user }),

  logout: () => {
    localStorage.clear()
    set({ user: null, isAuthenticated: false })
    window.location.href = '/login'
  },
}))

export default useAuthStore