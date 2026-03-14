import { useState, useEffect } from 'react'
import { History, MessageSquare, ChevronDown, ChevronUp, Trophy, Clock, Target, TrendingUp, Loader2, BookOpen } from 'lucide-react'
import { progressAPI, interviewAPI } from '../services/api'

function ScoreBadge({ score }) {
  if (score == null) return <span className="text-xs text-gray-500">—</span>
  const color = score >= 7 ? 'text-emerald-400' : score >= 5 ? 'text-amber-400' : 'text-red-400'
  return <span className={`text-sm font-bold ${color}`}>{score}/10</span>
}

function QuestionCard({ q, index }) {
  const [expanded, setExpanded] = useState(false)
  const scoreColor = q.score >= 7 ? 'border-emerald-500/30' : q.score >= 5 ? 'border-amber-500/30' : 'border-red-500/30'

  return (
    <div className={`border rounded-lg overflow-hidden ${q.score != null ? scoreColor : 'border-gray-700'}`}>
      <button onClick={() => setExpanded(!expanded)}
        className="w-full flex items-start justify-between px-4 py-3 hover:bg-gray-800/50 transition-colors text-left gap-3">
        <div className="flex items-start gap-3 flex-1">
          <span className="text-xs text-gray-500 mt-0.5 shrink-0">Q{index + 1}</span>
          <p className="text-sm text-gray-200">{q.question_text}</p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <ScoreBadge score={q.score} />
          {expanded ? <ChevronUp size={14} className="text-gray-500" /> : <ChevronDown size={14} className="text-gray-500" />}
        </div>
      </button>

      {expanded && (
        <div className="px-4 pb-4 space-y-3 border-t border-gray-800 pt-3">
          {q.answer_text && (
            <div>
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Your Answer</p>
              <p className="text-sm text-gray-300 leading-relaxed">{q.answer_text}</p>
            </div>
          )}
          {q.ai_feedback && (
            <div>
              <p className="text-xs font-semibold text-indigo-400 uppercase tracking-wider mb-1">AI Feedback</p>
              <p className="text-sm text-gray-300 leading-relaxed">{q.ai_feedback}</p>
            </div>
          )}
          {q.model_answer && (
            <div className="bg-emerald-600/10 border border-emerald-500/20 rounded-lg p-3">
              <p className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-1 flex items-center gap-1">
                <BookOpen size={11} /> Model Answer
              </p>
              <p className="text-sm text-gray-300 leading-relaxed">{q.model_answer}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function SessionCard({ session }) {
  const [expanded, setExpanded] = useState(false)
  const [questions, setQuestions] = useState(null)
  const [loadingQ, setLoadingQ] = useState(false)

  const handleExpand = async () => {
    setExpanded(!expanded)
    if (!expanded && !questions && session.status === 'completed') {
      setLoadingQ(true)
      try {
        const { data } = await interviewAPI.session(session.id)
        setQuestions(data.questions || [])
      } catch {
        setQuestions([])
      } finally {
        setLoadingQ(false)
      }
    }
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
      <button onClick={handleExpand}
        className="w-full flex items-center justify-between px-5 py-4 hover:bg-gray-800/50 transition-colors text-left">
        <div className="flex items-center gap-4">
          <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${session.type === 'behavioral' || session.type === 'hr' ? 'bg-indigo-600/20' : 'bg-purple-600/20'}`}>
            <MessageSquare size={16} className={session.type === 'behavioral' || session.type === 'hr' ? 'text-indigo-400' : 'text-purple-400'} />
          </div>
          <div>
            <p className="text-sm font-medium text-white capitalize">
              {session.type.replace(/_/g, ' ')} — {session.role.replace(/_/g, ' ')}
            </p>
            <div className="flex items-center gap-3 mt-0.5">
              <span className="text-xs text-gray-500">{session.date}</span>
              {session.duration_seconds && (
                <span className="text-xs text-gray-500 flex items-center gap-1">
                  <Clock size={10} />{Math.round(session.duration_seconds / 60)}m
                </span>
              )}
              <span className={`text-xs px-1.5 py-0.5 rounded capitalize ${
                session.status === 'completed' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-gray-700 text-gray-400'
              }`}>{session.status}</span>
              <span className="text-xs px-1.5 py-0.5 rounded capitalize bg-gray-800 text-gray-400">
                {session.difficulty}
              </span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <ScoreBadge score={session.score} />
          {expanded ? <ChevronUp size={16} className="text-gray-500" /> : <ChevronDown size={16} className="text-gray-500" />}
        </div>
      </button>

      {expanded && session.status === 'completed' && (
        <div className="px-5 pb-5 border-t border-gray-800 pt-4 space-y-4">
          {session.summary && (
            <p className="text-sm text-gray-300 leading-relaxed">{session.summary}</p>
          )}

          <div className="grid grid-cols-2 gap-4">
            {session.strengths?.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-2">Strengths</p>
                <ul className="space-y-1.5">
                  {session.strengths.map((s, i) => (
                    <li key={i} className="text-xs text-gray-300 flex items-start gap-2">
                      <span className="text-emerald-400 mt-0.5">✓</span>{s}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {session.improvements?.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-amber-400 uppercase tracking-wider mb-2">Improvements</p>
                <ul className="space-y-1.5">
                  {session.improvements.map((s, i) => (
                    <li key={i} className="text-xs text-gray-300 flex items-start gap-2">
                      <span className="text-amber-400 mt-0.5">→</span>{s}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Q&A Section */}
          <div>
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Questions & Answers</p>
            {loadingQ ? (
              <div className="flex items-center gap-2 text-gray-500 text-sm">
                <Loader2 size={14} className="animate-spin" /> Loading questions...
              </div>
            ) : questions?.length > 0 ? (
              <div className="space-y-2">
                {questions.map((q, i) => <QuestionCard key={q.id} q={q} index={i} />)}
              </div>
            ) : (
              <p className="text-xs text-gray-500">No questions recorded.</p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default function HistoryPage() {
  const [history, setHistory] = useState([])
  const [dashboard, setDashboard] = useState(null)
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')

  useEffect(() => {
    Promise.all([progressAPI.history(), progressAPI.dashboard()])
      .then(([h, d]) => { setHistory(h.data); setDashboard(d.data) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const filtered = filter === 'all' ? history : history.filter(s => s.type === filter)

  if (loading) return (
    <div className="flex items-center justify-center h-full">
      <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
    </div>
  )

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Interview History</h1>
        <p className="text-gray-400 mt-1">Track your progress and review model answers</p>
      </div>

      {dashboard && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <History size={14} className="text-indigo-400" />
              <p className="text-xs text-gray-400">Total Sessions</p>
            </div>
            <p className="text-2xl font-bold text-white">{dashboard.interview_stats.total_sessions}</p>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <Trophy size={14} className="text-amber-400" />
              <p className="text-xs text-gray-400">Average Score</p>
            </div>
            <p className="text-2xl font-bold text-white">{dashboard.interview_stats.average_score || '—'}</p>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <Target size={14} className="text-emerald-400" />
              <p className="text-xs text-gray-400">Best Score</p>
            </div>
            <p className="text-2xl font-bold text-white">{dashboard.interview_stats.best_score || '—'}</p>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp size={14} className="text-purple-400" />
              <p className="text-xs text-gray-400">Completed</p>
            </div>
            <p className="text-2xl font-bold text-white">{dashboard.interview_stats.completed_sessions}</p>
          </div>
        </div>
      )}

      <div className="flex gap-2 mb-5">
        {['all', 'behavioral', 'technical', 'system_design', 'hr'].map(f => (
          <button key={f} onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-colors ${
              filter === f ? 'bg-indigo-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-white'
            }`}>
            {f.replace('_', ' ')}
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <div className="text-center py-16">
          <History size={40} className="text-gray-700 mx-auto mb-4" />
          <p className="text-gray-400">No sessions found</p>
          <p className="text-gray-600 text-sm mt-1">Complete an interview to see it here</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map(session => (
            <SessionCard key={session.id} session={session} />
          ))}
        </div>
      )}
    </div>
  )
}