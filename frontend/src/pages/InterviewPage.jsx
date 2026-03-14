import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  MessageSquare, Video, Code2, TrendingUp, Trophy,
  Target, Clock, Zap, ChevronRight, BarChart2
} from 'lucide-react'
import { progressAPI } from '../services/api'
import useAuthStore from '../store/authStore'

// Simple bar chart using divs (no extra library needed)
function ScoreBarChart({ data }) {
  if (!data?.length) return <p className="text-sm text-gray-500 text-center py-6">No data yet</p>
  const max = 10
  return (
    <div className="space-y-2">
      {data.map((d, i) => (
        <div key={i} className="flex items-center gap-3">
          <p className="text-xs text-gray-400 w-20 truncate shrink-0">{d.label}</p>
          <div className="flex-1 h-5 bg-gray-800 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-700 ${d.score >= 7 ? 'bg-emerald-500' : d.score >= 5 ? 'bg-amber-500' : 'bg-red-500'}`}
              style={{ width: `${(d.score / max) * 100}%` }}
            />
          </div>
          <p className={`text-xs font-bold w-8 text-right ${d.score >= 7 ? 'text-emerald-400' : d.score >= 5 ? 'text-amber-400' : 'text-red-400'}`}>
            {d.score}
          </p>
        </div>
      ))}
    </div>
  )
}

// Line sparkline using SVG
function ScoreSparkline({ scores }) {
  if (!scores?.length || scores.length < 2) return (
    <p className="text-xs text-gray-500 text-center py-4">Complete more sessions to see trend</p>
  )
  const w = 300, h = 60, pad = 8
  const min = Math.min(...scores) - 1
  const max = Math.max(...scores) + 1
  const points = scores.map((s, i) => {
    const x = pad + (i / (scores.length - 1)) * (w - pad * 2)
    const y = h - pad - ((s - min) / (max - min)) * (h - pad * 2)
    return `${x},${y}`
  })
  const lastScore = scores[scores.length - 1]
  const trend = scores.length > 1 ? lastScore - scores[scores.length - 2] : 0

  return (
    <div>
      <svg viewBox={`0 0 ${w} ${h}`} className="w-full">
        <polyline fill="none" stroke="#6366f1" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
          points={points.join(' ')} />
        {points.map((p, i) => {
          const [x, y] = p.split(',')
          return <circle key={i} cx={x} cy={y} r="3" fill="#6366f1" />
        })}
      </svg>
      <div className="flex items-center justify-between mt-1">
        <p className="text-xs text-gray-500">Last {scores.length} sessions</p>
        <p className={`text-xs font-medium ${trend > 0 ? 'text-emerald-400' : trend < 0 ? 'text-red-400' : 'text-gray-400'}`}>
          {trend > 0 ? `↑ +${trend.toFixed(1)}` : trend < 0 ? `↓ ${trend.toFixed(1)}` : '→ Stable'}
        </p>
      </div>
    </div>
  )
}

// Donut chart
function DonutChart({ value, max = 10, size = 80, color = '#6366f1' }) {
  const r = (size - 10) / 2
  const circ = 2 * Math.PI * r
  const dash = (value / max) * circ
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="#1f2937" strokeWidth={10} />
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth={10}
          strokeDasharray={`${dash} ${circ}`} strokeLinecap="round"
          style={{ transition: 'stroke-dasharray 1s ease' }} />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <p className="text-base font-black" style={{ color }}>{value || '—'}</p>
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const [dashboard, setDashboard] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    progressAPI.dashboard()
      .then(r => setDashboard(r.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const stats = dashboard?.interview_stats
  const recentSessions = dashboard?.recent_sessions || []

  // Build bar chart data from recent sessions
  const barData = recentSessions
    .filter(s => s.score)
    .slice(0, 6)
    .map((s, i) => ({
      label: `#${recentSessions.length - i}`,
      score: parseFloat(s.score),
    }))
    .reverse()

  // Scores array for sparkline
  const scoreHistory = recentSessions
    .filter(s => s.score)
    .map(s => parseFloat(s.score))
    .reverse()

  // Type breakdown
  const typeBreakdown = recentSessions.reduce((acc, s) => {
    acc[s.type] = (acc[s.type] || 0) + 1
    return acc
  }, {})

  const quickActions = [
    { label: 'Concept Review', icon: MessageSquare, color: 'bg-indigo-600', path: '/interview' },
    { label: 'Video Interview', icon: Video, color: 'bg-rose-600', path: '/video-interview' },
    { label: 'Coding Challenge', icon: Code2, color: 'bg-purple-600', path: '/coding' },
  ]

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">
            Welcome back, {user?.full_name?.split(' ')[0]} 👋
          </h1>
          <p className="text-gray-400 mt-0.5 text-sm capitalize">
            {user?.target_role?.replace(/_/g, ' ')} · {user?.experience_level}
          </p>
        </div>
        <button onClick={() => navigate('/history')}
          className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-xl text-sm transition-colors">
          <BarChart2 size={15} />View Full History
        </button>
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-3 gap-4">
        {quickActions.map(({ label, icon: Icon, color, path }) => (
          <button key={path} onClick={() => navigate(path)}
            className="flex items-center gap-3 p-4 bg-gray-900 border border-gray-800 rounded-xl hover:border-gray-600 transition-all group">
            <div className={`w-10 h-10 ${color} rounded-xl flex items-center justify-center shrink-0`}>
              <Icon size={18} className="text-white" />
            </div>
            <div className="text-left">
              <p className="text-sm font-medium text-white">{label}</p>
              <p className="text-xs text-gray-500">Start now</p>
            </div>
            <ChevronRight size={14} className="text-gray-600 ml-auto group-hover:text-gray-400 transition-colors" />
          </button>
        ))}
      </div>

      {/* Score cards row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Total Sessions', value: stats?.total_sessions || 0, icon: Clock, color: '#6366f1' },
          { label: 'Avg Score', value: stats?.average_score || 0, icon: TrendingUp, color: '#10b981', max: 10 },
          { label: 'Best Score', value: stats?.best_score || 0, icon: Trophy, color: '#f59e0b', max: 10 },
          { label: 'Completed', value: stats?.completed_sessions || 0, icon: Target, color: '#8b5cf6' },
        ].map(({ label, value, icon: Icon, color, max }) => (
          <div key={label} className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex items-center gap-4">
            {max ? (
              <DonutChart value={value} max={max} size={64} color={color} />
            ) : (
              <div className="w-16 h-16 rounded-full flex items-center justify-center shrink-0" style={{ background: `${color}20` }}>
                <p className="text-xl font-black" style={{ color }}>{value}</p>
              </div>
            )}
            <div>
              <p className="text-xs text-gray-400">{label}</p>
              <Icon size={14} className="mt-1" style={{ color }} />
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Score trend */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp size={15} className="text-indigo-400" />
            <p className="text-sm font-semibold text-white">Score Trend</p>
          </div>
          <ScoreSparkline scores={scoreHistory} />
        </div>

        {/* Score by session */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <BarChart2 size={15} className="text-purple-400" />
            <p className="text-sm font-semibold text-white">Recent Scores</p>
          </div>
          <ScoreBarChart data={barData} />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Interview type breakdown */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <Zap size={15} className="text-amber-400" />
            <p className="text-sm font-semibold text-white">Practice Breakdown</p>
          </div>
          {Object.keys(typeBreakdown).length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-4">No sessions yet</p>
          ) : (
            <div className="space-y-2">
              {Object.entries(typeBreakdown).map(([type, count]) => {
                const total = recentSessions.length
                const pct = Math.round((count / total) * 100)
                return (
                  <div key={type} className="flex items-center gap-3">
                    <p className="text-xs text-gray-400 w-28 capitalize shrink-0">{type.replace(/_/g, ' ')}</p>
                    <div className="flex-1 h-4 bg-gray-800 rounded-full overflow-hidden">
                      <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${pct}%` }} />
                    </div>
                    <p className="text-xs text-gray-400 w-8 text-right">{count}</p>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Recent sessions */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm font-semibold text-white">Recent Sessions</p>
            <button onClick={() => navigate('/history')} className="text-xs text-indigo-400 hover:text-indigo-300">View all</button>
          </div>
          {recentSessions.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-4">No sessions yet — start practicing!</p>
          ) : (
            <div className="space-y-2">
              {recentSessions.slice(0, 4).map((s, i) => (
                <div key={i} className="flex items-center justify-between py-2 border-b border-gray-800 last:border-0">
                  <div>
                    <p className="text-xs font-medium text-white capitalize">{s.type?.replace(/_/g, ' ')}</p>
                    <p className="text-xs text-gray-500">{s.date}</p>
                  </div>
                  {s.score ? (
                    <span className={`text-sm font-bold ${s.score >= 7 ? 'text-emerald-400' : s.score >= 5 ? 'text-amber-400' : 'text-red-400'}`}>
                      {s.score}/10
                    </span>
                  ) : (
                    <span className="text-xs text-gray-600">—</span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}