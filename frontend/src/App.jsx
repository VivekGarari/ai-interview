import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import useAuthStore from './store/authStore'

import LoginPage from './pages/LoginPage'
import SignupPage from './pages/SignupPage'
import DashboardPage from './pages/DashboardPage'
import InterviewPage from './pages/InterviewPage'
import VideoInterviewPage from './pages/VideoInterviewPage'
import CodingPage from './pages/CodingPage'
import HistoryPage from './pages/HistoryPage'
import MockExamPage from './pages/MockExamPage'
import SettingsPage from './pages/SettingsPage'
import Layout from './components/layout/Layout'

function PrivateRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuthStore()
  if (isLoading) return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950">
      <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
    </div>
  )
  return isAuthenticated ? children : <Navigate to="/login" replace />
}

export default function App() {
  const init = useAuthStore((s) => s.init)
  useEffect(() => { init() }, [])

  return (
    <BrowserRouter>
      <Toaster position="top-right" toastOptions={{
        style: { background: '#1e1e2e', color: '#cdd6f4', border: '1px solid #313244' }
      }} />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/" element={
          <PrivateRoute>
            <Layout />
          </PrivateRoute>
        }>
          <Route index element={<DashboardPage />} />
          <Route path="interview" element={<InterviewPage />} />
          <Route path="video-interview" element={<VideoInterviewPage />} />
          <Route path="coding" element={<CodingPage />} />
          <Route path="history" element={<HistoryPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="exam" element={<MockExamPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}