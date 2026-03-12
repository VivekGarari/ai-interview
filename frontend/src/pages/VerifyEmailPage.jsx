import { useState, useRef, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Brain, Loader2, RefreshCw, CheckCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import { authAPI } from '../services/api'
import useAuthStore from '../store/authStore'

export default function VerifyEmailPage() {
  const [otp, setOtp] = useState(['', '', '', '', '', ''])
  const [loading, setLoading] = useState(false)
  const [resending, setResending] = useState(false)
  const [verified, setVerified] = useState(false)
  const [countdown, setCountdown] = useState(60)
  const [canResend, setCanResend] = useState(false)
  const inputs = useRef([])
  const navigate = useNavigate()
  const { user, setUser } = useAuthStore()
  const email = user?.email || ''

  // Countdown for resend button
  useEffect(() => {
    if (countdown <= 0) { setCanResend(true); return }
    const t = setTimeout(() => setCountdown(c => c - 1), 1000)
    return () => clearTimeout(t)
  }, [countdown])

  const handleChange = (i, val) => {
    if (!/^\d*$/.test(val)) return
    const newOtp = [...otp]
    newOtp[i] = val.slice(-1)
    setOtp(newOtp)
    if (val && i < 5) inputs.current[i + 1]?.focus()
    // Auto submit when all filled
    if (newOtp.every(d => d) && newOtp.join('').length === 6) {
      handleVerify(newOtp.join(''))
    }
  }

  const handleKeyDown = (i, e) => {
    if (e.key === 'Backspace' && !otp[i] && i > 0) {
      inputs.current[i - 1]?.focus()
    }
  }

  const handlePaste = (e) => {
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6)
    if (pasted.length === 6) {
      setOtp(pasted.split(''))
      handleVerify(pasted)
    }
  }

  const handleVerify = async (code) => {
    if (loading) return
    setLoading(true)
    try {
      await authAPI.verifyEmail({ email, otp: code })
      setVerified(true)
      setUser({ ...user, is_verified: true })
      toast.success('Email verified!')
      setTimeout(() => navigate('/'), 1500)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Invalid OTP')
      setOtp(['', '', '', '', '', ''])
      inputs.current[0]?.focus()
    } finally {
      setLoading(false)
    }
  }

  const resend = async () => {
    if (!canResend) return
    setResending(true)
    try {
      await authAPI.resendOTP({ email })
      toast.success('New OTP sent!')
      setCountdown(60)
      setCanResend(false)
      setOtp(['', '', '', '', '', ''])
      inputs.current[0]?.focus()
    } catch {
      toast.error('Failed to resend OTP')
    } finally {
      setResending(false)
    }
  }

  if (verified) return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <div className="text-center">
        <div className="w-16 h-16 bg-emerald-600/20 rounded-full flex items-center justify-center mx-auto mb-4">
          <CheckCircle size={32} className="text-emerald-400" />
        </div>
        <p className="text-xl font-bold text-white">Email Verified!</p>
        <p className="text-gray-400 text-sm mt-1">Redirecting to dashboard...</p>
      </div>
    </div>
  )

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-indigo-600 rounded-2xl mb-4">
            <Brain size={28} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">Verify your email</h1>
          <p className="text-gray-400 mt-2 text-sm">
            We sent a 6-digit code to<br />
            <span className="text-indigo-400 font-medium">{email}</span>
          </p>
        </div>

        <div className="bg-gray-900 rounded-2xl p-8 border border-gray-800">
          {/* OTP inputs */}
          <div className="flex gap-3 justify-center mb-6" onPaste={handlePaste}>
            {otp.map((digit, i) => (
              <input
                key={i}
                ref={el => inputs.current[i] = el}
                type="text"
                inputMode="numeric"
                maxLength={1}
                value={digit}
                onChange={e => handleChange(i, e.target.value)}
                onKeyDown={e => handleKeyDown(i, e)}
                className={`w-12 h-14 text-center text-xl font-bold bg-gray-800 border rounded-xl text-white focus:outline-none transition-all ${
                  digit ? 'border-indigo-500 bg-indigo-600/10' : 'border-gray-700 focus:border-indigo-500'
                }`}
              />
            ))}
          </div>

          <button
            onClick={() => handleVerify(otp.join(''))}
            disabled={loading || otp.join('').length !== 6}
            className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold py-2.5 rounded-xl transition-colors flex items-center justify-center gap-2 mb-4">
            {loading ? <Loader2 size={18} className="animate-spin" /> : null}
            {loading ? 'Verifying...' : 'Verify Email'}
          </button>

          <div className="text-center">
            {canResend ? (
              <button onClick={resend} disabled={resending}
                className="flex items-center gap-2 text-sm text-indigo-400 hover:text-indigo-300 transition-colors mx-auto">
                {resending ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
                Resend code
              </button>
            ) : (
              <p className="text-sm text-gray-500">
                Resend code in <span className="text-gray-300">{countdown}s</span>
              </p>
            )}
          </div>
        </div>

        <p className="text-center text-xs text-gray-600 mt-4">
          Wrong email?{' '}
          <button onClick={() => { useAuthStore.getState().logout() }}
            className="text-indigo-400 hover:text-indigo-300">
            Sign out
          </button>
        </p>
      </div>
    </div>
  )
}