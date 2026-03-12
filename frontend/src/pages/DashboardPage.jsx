import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { MessageSquare, Video, Code2, TrendingUp, Trophy, Target, Clock, ChevronRight } from 'lucide-react'
import { progressAPI } from '../services/api'
import useAuthStore from '../store/authStore'

function StatCard({ icon: Icon, label, value, color }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <div className={`inline-flex p-2 rounded-lg ${color} mb-3`}>
        <Icon size={18} className="text-white" />
      </div>
      <p className="text-2xl font-bold text-white">{value ?? '—'}</p>
      <p className="text-sm text-gray-400 mt-0.5">{label}</p>
    </div>
  )
}

function ActionCard({ icon: Icon, title, desc, color, onClick }) {
  return (
    <button onClick={onClick}
      className="bg-gray-900 border border-gray-800 hover:border-indigo-500 rounded-xl p-5 text-left transition-all group w-full">
      <div className={`inline-flex p-2.5 rounded-lg ${color} mb-3`}>
        <Icon size={20} className="text-white" />
      </div>
      <div className="flex items-center justify-between">
        <div>
          <p className="font-semibold text-white">{title}</p>
          <p className="text-sm text-gray-400 mt-0.5">{desc}</p>
        </div>
        <ChevronRight size={18} className="text-gray-600 group-hover:text-indigo-400 transition-colors" />
      </div>
    </button>
  )
}

export default function DashboardPage() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    progressAPI.dashboard()
      .then((r) => setStats(r.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="p-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">
          Welcome back, {user?.full_name?.split(' ')[0]}! 👋
        </h1>
        <p className="text-gray-400 mt-1">
          Ready to practice? Your target role is{' '}
          <span className="text-indigo-400 font-medium">
            {user?.target_role?.replace(/_/g, ' ')}
          </span>
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard icon={MessageSquare} label="Total Sessions" color="bg-indigo-600"
          value={stats?.interview_stats?.total_sessions} />
        <StatCard icon={Trophy} label="Average Score" color="bg-amber-600"
          value={stats?.interview_stats?.average_score ? `${stats.interview_stats.average_score}/10` : null} />
        <StatCard icon={Target} label="Best Score" color="bg-green-600"
          value={stats?.interview_stats?.best_score ? `${stats.interview_stats.best_score}/10` : null} />
        <StatCard icon={Code2} label="Code Submissions" color="bg-purple-600"
          value={stats?.coding_stats?.total_submissions} />
      </div>

      {/* Quick actions */}
      <h2 className="text-lg font-semibold text-white mb-4">Start Practicing</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <ActionCard icon={MessageSquare} color="bg-indigo-600"
          title="Text Interview" desc="AI interviews via text chat"
          onClick={() => navigate('/interview')} />
        <ActionCard icon={Video} color="bg-rose-600"
          title="Video Interview" desc="Real-time voice + camera interview"
          onClick={() => navigate('/video-interview')} />
        <ActionCard icon={Code2} color="bg-purple-600"
          title="Coding Challenge" desc="AI-generated coding problems"
          onClick={() => navigate('/coding')} />
      </div>

      {/* Recent sessions */}
      {stats?.recent_sessions?.length > 0 && (
        <>
          <h2 className="text-lg font-semibold text-white mb-4">Recent Sessions</h2>
          <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
            {stats.recent_sessions.map((s, i) => (
              <div key={s.id}
                className={`flex items-center justify-between px-5 py-4 ${i !== 0 ? 'border-t border-gray-800' : ''}`}>
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-indigo-600/20 rounded-lg flex items-center justify-center">
                    <MessageSquare size={14} className="text-indigo-400" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-white capitalize">
                      {s.type.replace('_', ' ')} — {s.role.replace(/_/g, ' ')}
                    </p>
                    <p className="text-xs text-gray-400">{s.date}</p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  {s.duration_seconds && (
                    <span className="text-xs text-gray-400 flex items-center gap-1">
                      <Clock size={12} />
                      {Math.round(s.duration_seconds / 60)}m
                    </span>
                  )}
                  {s.score && (
                    <span className={`text-sm font-bold ${s.score >= 7 ? 'text-green-400' : s.score >= 5 ? 'text-amber-400' : 'text-red-400'}`}>
                      {s.score}/10
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}