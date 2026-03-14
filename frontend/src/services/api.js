import axios from 'axios'

const api = axios.create({
  baseURL: 'https://proctoai-backend.onrender.com',
  headers: { 'Content-Type': 'application/json' },
})

// Auto-attach token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Auto-refresh on 401
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401) {
      const refresh = localStorage.getItem('refresh_token')
      if (refresh) {
        try {
          const { data } = await axios.post('https://proctoai-backend.onrender.com/auth/refresh', {
            refresh_token: refresh,
          })
          localStorage.setItem('access_token', data.access_token)
          localStorage.setItem('refresh_token', data.refresh_token)
          error.config.headers.Authorization = `Bearer ${data.access_token}`
          return api(error.config)
        } catch {
          localStorage.clear()
          window.location.href = '/login'
        }
      } else {
        localStorage.clear()
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// ── Auth ──────────────────────────────────────────────
export const authAPI = {
  signup: (data) => api.post('/auth/signup', data),
  login: (data) => api.post('/auth/login', data),
  me: () => api.get("/auth/me"),
  updateMe: (data) => api.patch("/auth/me", data),
  changePassword: (data) => api.post("/auth/change-password", data),
  verifyEmail: (data) => api.post('/auth/verify-email', data),
  resendOTP: (data) => api.post('/auth/resend-otp', data),
  logout: () => api.post('/auth/logout'),
}

// ── Interview ─────────────────────────────────────────
export const interviewAPI = {
  start: (data) => api.post('/interview/start', data),
  answer: (data) => api.post('/interview/answer', data),
  end: (data) => api.post('/interview/end', data),
  sessions: () => api.get('/interview/sessions'),
  session: (id) => api.get(`/interview/session/${id}`),
}

// ── Video Interview ───────────────────────────────────
export const videoAPI = {
  start: (data) => api.post('/video/start', data),
  transcribe: (formData) => api.post('/video/transcribe', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  uploadRecording: (formData) => api.post('/video/upload-recording', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  end: (sessionId) => api.post(`/video/end?session_id=${sessionId}`),
  questionAudioUrl: (questionId) => `https://proctoai-backend.onrender.com/video/question/${questionId}/audio`,
}

// ── Coding ────────────────────────────────────────────
export const codingAPI = {
  problems: (filters) => api.get('/coding/problems', { params: filters }),
  generate: (data) => api.post('/coding/generate', data),
  run: (data) => api.post('/coding/run', data),
  submit: (data) => api.post('/coding/submit', data),
  submissions: () => api.get('/coding/submissions'),
}

// ── Progress ──────────────────────────────────────────
export const progressAPI = {
  dashboard: () => api.get('/progress/dashboard'),
  history: () => api.get('/progress/history'),
}

export default api

// ── Mock Exam ──────────────────────────────────────────
export const examAPI = {
  start: (data) => api.post('/exam/start', data),
  submit: (data) => api.post('/exam/submit', data),
}

// ── Resume ─────────────────────────────────────────────
export const resumeAPI = {
  analyze: (formData) => api.post('/resume/analyze', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
}

// already in authAPI — adding verify methods
// authAPI.verifyEmail and authAPI.resendOTP added below via patch