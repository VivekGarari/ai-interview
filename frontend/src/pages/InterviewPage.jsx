import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Send, Loader2, ChevronRight, Trophy, MessageSquare, RotateCcw, CheckCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import { interviewAPI } from '../services/api'
import useAuthStore from '../store/authStore'

const TYPES = [
  { value: 'behavioral', label: 'Behavioral', desc: 'Situation-based questions' },
  { value: 'technical', label: 'Technical', desc: 'System design & concepts' },
  { value: 'system_design', label: 'System Design', desc: 'Architecture & scalability' },
  { value: 'hr', label: 'HR Round', desc: 'Culture fit & motivation' },
]

const DIFFICULTIES = ['easy', 'medium', 'hard']

function ScoreBar({ score }) {
  const color = score >= 7 ? 'bg-emerald-500' : score >= 5 ? 'bg-amber-500' : 'bg-red-500'
  return (
    <div className="mt-2">
      <div className="flex justify-between text-xs text-gray-400 mb-1">
        <span>Score</span>
        <span className={score >= 7 ? 'text-emerald-400' : score >= 5 ? 'text-amber-400' : 'text-red-400'}>
          {score}/10
        </span>
      </div>
      <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all duration-700`} style={{ width: `${score * 10}%` }} />
      </div>
    </div>
  )
}

function FeedbackCard({ feedback }) {
  return (
    <div className="mt-3 bg-gray-800/60 border border-gray-700 rounded-xl p-4 space-y-2">
      <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">AI Feedback</p>
      <p className="text-sm text-gray-300 leading-relaxed">{feedback.feedback}</p>
      <ScoreBar score={feedback.score} />
      {feedback.follow_up && (
        <div className="mt-3 pt-3 border-t border-gray-700">
          <p className="text-xs text-indigo-400 font-medium mb-1">Follow-up question:</p>
          <p className="text-sm text-gray-300 italic">"{feedback.follow_up}"</p>
        </div>
      )}
    </div>
  )
}

function ReportModal({ report, onClose, onRestart }) {
  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-lg p-8">
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-indigo-600/20 mb-4">
            <Trophy size={28} className="text-indigo-400" />
          </div>
          <h2 className="text-2xl font-bold text-white">Interview Complete!</h2>
          <div className="mt-2">
            <span className={`text-4xl font-black ${report.overall_score >= 7 ? 'text-emerald-400' : report.overall_score >= 5 ? 'text-amber-400' : 'text-red-400'}`}>
              {report.overall_score}
            </span>
            <span className="text-xl text-gray-500">/10</span>
          </div>
        </div>
        <p className="text-gray-300 text-sm leading-relaxed mb-6 text-center">{report.summary}</p>
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="bg-gray-800 rounded-xl p-4">
            <p className="text-xs text-emerald-400 font-semibold uppercase tracking-wider mb-2">Strengths</p>
            <ul className="space-y-1.5">
              {report.strengths?.map((s, i) => (
                <li key={i} className="flex items-start gap-2 text-xs text-gray-300">
                  <CheckCircle size={12} className="text-emerald-400 mt-0.5 shrink-0" />{s}
                </li>
              ))}
            </ul>
          </div>
          <div className="bg-gray-800 rounded-xl p-4">
            <p className="text-xs text-amber-400 font-semibold uppercase tracking-wider mb-2">Improve</p>
            <ul className="space-y-1.5">
              {report.improvements?.map((s, i) => (
                <li key={i} className="flex items-start gap-2 text-xs text-gray-300">
                  <ChevronRight size={12} className="text-amber-400 mt-0.5 shrink-0" />{s}
                </li>
              ))}
            </ul>
          </div>
        </div>
        <div className="flex gap-3">
          <button onClick={onClose} className="flex-1 px-4 py-2.5 bg-gray-800 hover:bg-gray-700 text-white rounded-xl text-sm font-medium transition-colors">
            View History
          </button>
          <button onClick={onRestart} className="flex-1 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-medium transition-colors flex items-center justify-center gap-2">
            <RotateCcw size={14} />New Interview
          </button>
        </div>
      </div>
    </div>
  )
}

export default function InterviewPage() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const [phase, setPhase] = useState('setup')
  const [config, setConfig] = useState({
    interview_type: 'behavioral',
    target_role: user?.target_role?.replace(/_/g, ' ') || 'software engineer',
    difficulty: 'medium',
  })
  const [session, setSession] = useState(null)
  const [messages, setMessages] = useState([])
  const [currentQuestion, setCurrentQuestion] = useState(null)
  const [answer, setAnswer] = useState('')
  const [loading, setLoading] = useState(false)
  const [report, setReport] = useState(null)
  const [questionsAnswered, setQuestionsAnswered] = useState(0)
  const bottomRef = useRef(null)

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const startInterview = async () => {
    setLoading(true)
    try {
      const { data } = await interviewAPI.start({
        interview_type: config.interview_type,
        target_role: config.target_role,
        difficulty: config.difficulty,
      })
      setSession(data)
      setCurrentQuestion(data.question)
      setMessages([{ type: 'question', text: data.question.question_text, id: data.question.id }])
      setPhase('interview')
    } catch { toast.error('Failed to start interview') }
    finally { setLoading(false) }
  }

  const submitAnswer = async () => {
    if (!answer.trim() || loading) return
    const myAnswer = answer.trim()
    setAnswer('')
    setLoading(true)
    setMessages((m) => [...m, { type: 'answer', text: myAnswer }])
    try {
      const { data } = await interviewAPI.answer({
        session_id: session.session_id,
        question_id: currentQuestion.id,
        answer_text: myAnswer,
      })
      setQuestionsAnswered(data.questions_answered + 1)
      setMessages((m) => [...m, { type: 'feedback', data: data.feedback }])
      if (data.session_complete || data.questions_answered >= 4) {
        const { data: rep } = await interviewAPI.end({ session_id: session.session_id })
        setReport(rep)
        setPhase('done')
      } else {
        setCurrentQuestion(data.next_question)
        setMessages((m) => [...m, { type: 'question', text: data.next_question.question_text, id: data.next_question.id }])
      }
    } catch { toast.error('Failed to submit answer') }
    finally { setLoading(false) }
  }

  const restart = () => {
    setPhase('setup'); setSession(null); setMessages([])
    setCurrentQuestion(null); setAnswer(''); setReport(null); setQuestionsAnswered(0)
  }

  if (phase === 'setup') return (
    <div className="p-8 max-w-2xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Concept Review</h1>
        <p className="text-gray-400 mt-1">Configure your AI interview session</p>
      </div>
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-3">Interview Type</label>
          <div className="grid grid-cols-2 gap-3">
            {TYPES.map((t) => (
              <button key={t.value} onClick={() => setConfig({ ...config, interview_type: t.value })}
                className={`p-3 rounded-xl border text-left transition-all ${config.interview_type === t.value ? 'border-indigo-500 bg-indigo-600/10' : 'border-gray-700 hover:border-gray-600'}`}>
                <p className="text-sm font-medium text-white">{t.label}</p>
                <p className="text-xs text-gray-400 mt-0.5">{t.desc}</p>
              </button>
            ))}
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Target Role</label>
          <input value={config.target_role} onChange={(e) => setConfig({ ...config, target_role: e.target.value })}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 transition-colors"
            placeholder="e.g. Software Engineer" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-3">Difficulty</label>
          <div className="flex gap-3">
            {DIFFICULTIES.map((d) => (
              <button key={d} onClick={() => setConfig({ ...config, difficulty: d })}
                className={`flex-1 py-2 rounded-lg text-sm font-medium capitalize transition-all ${config.difficulty === d ? 'bg-indigo-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'}`}>
                {d}
              </button>
            ))}
          </div>
        </div>
        <button onClick={startInterview} disabled={loading}
          className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold py-3 rounded-xl transition-colors flex items-center justify-center gap-2">
          {loading ? <Loader2 size={18} className="animate-spin" /> : <MessageSquare size={18} />}
          {loading ? 'Starting...' : 'Start Interview'}
        </button>
      </div>
    </div>
  )

  return (
    <div className="flex flex-col h-full">
      <div className="px-6 py-4 border-b border-gray-800 bg-gray-900 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <MessageSquare size={18} className="text-indigo-400" />
          <span className="font-medium text-white capitalize">{config.interview_type.replace('_', ' ')} Interview</span>
          <span className="text-xs px-2 py-0.5 bg-gray-800 text-gray-400 rounded-full capitalize">{config.difficulty}</span>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-400">{questionsAnswered}/5 answered</span>
          <div className="w-24 h-1.5 bg-gray-800 rounded-full overflow-hidden">
            <div className="h-full bg-indigo-500 rounded-full transition-all duration-500" style={{ width: `${(questionsAnswered / 5) * 100}%` }} />
          </div>
          <button onClick={restart} className="text-xs text-gray-500 hover:text-gray-300 transition-colors">End</button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4">
        {messages.map((msg, i) => {
          if (msg.type === 'question') return (
            <div key={i} className="flex gap-3 max-w-2xl">
              <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center shrink-0 mt-1">
                <MessageSquare size={14} className="text-white" />
              </div>
              <div className="bg-gray-900 border border-gray-800 rounded-2xl rounded-tl-sm px-4 py-3">
                <p className="text-sm text-gray-300 leading-relaxed">{msg.text}</p>
              </div>
            </div>
          )
          if (msg.type === 'answer') return (
            <div key={i} className="flex gap-3 max-w-2xl ml-auto flex-row-reverse">
              <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center shrink-0 mt-1 text-sm font-bold text-white">
                {user?.full_name?.[0]?.toUpperCase()}
              </div>
              <div className="bg-indigo-600/20 border border-indigo-500/30 rounded-2xl rounded-tr-sm px-4 py-3">
                <p className="text-sm text-gray-200 leading-relaxed">{msg.text}</p>
              </div>
            </div>
          )
          if (msg.type === 'feedback') return (
            <div key={i} className="max-w-2xl">
              <FeedbackCard feedback={msg.data} />
            </div>
          )
        })}
        {loading && (
          <div className="flex gap-3 max-w-2xl">
            <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center shrink-0">
              <Loader2 size={14} className="text-white animate-spin" />
            </div>
            <div className="bg-gray-900 border border-gray-800 rounded-2xl rounded-tl-sm px-4 py-3">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="px-6 py-4 border-t border-gray-800 bg-gray-900">
        <div className="flex gap-3 max-w-3xl mx-auto">
          <textarea value={answer} onChange={(e) => setAnswer(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) submitAnswer() }}
            disabled={loading} placeholder="Type your answer... (Ctrl+Enter to submit)" rows={3}
            className="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 transition-colors resize-none text-sm" />
          <button onClick={submitAnswer} disabled={loading || !answer.trim()}
            className="px-4 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white rounded-xl transition-colors flex items-center justify-center">
            <Send size={18} />
          </button>
        </div>
        <p className="text-xs text-gray-600 text-center mt-2">Ctrl+Enter to submit</p>
      </div>

      {report && <ReportModal report={report} onClose={() => navigate('/history')} onRestart={restart} />}
    </div>
  )
}