import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Clock, CheckCircle, XCircle, AlertTriangle, Trophy,
  ChevronRight, ChevronLeft, Loader2, BookOpen, RotateCcw, Send
} from 'lucide-react'
import toast from 'react-hot-toast'
import { examAPI } from '../services/api'
import useAuthStore from '../store/authStore'
import { CODING_TOPICS, ROLES } from '../data/options'

const DIFFICULTIES = ['easy', 'medium', 'hard']
const Q_TYPES = [
  { value: 'mcq', label: 'MCQ' },
  { value: 'short_answer', label: 'Short Answer' },
  { value: 'coding', label: 'Coding' },
]

const groupedTopics = CODING_TOPICS.reduce((acc, t) => {
  if (!acc[t.group]) acc[t.group] = []
  acc[t.group].push(t)
  return acc
}, {})

const groupedRoles = ROLES.reduce((acc, r) => {
  if (!acc[r.group]) acc[r.group] = []
  acc[r.group].push(r)
  return acc
}, {})

// ── Timer ──────────────────────────────────────────────
function Timer({ seconds, warning, onExpire }) {
  const [remaining, setRemaining] = useState(seconds)
  const ref = useRef()

  useEffect(() => {
    setRemaining(seconds)
  }, [seconds])

  useEffect(() => {
    if (remaining <= 0) { onExpire?.(); return }
    ref.current = setInterval(() => setRemaining(r => {
      if (r <= 1) { clearInterval(ref.current); onExpire?.(); return 0 }
      return r - 1
    }), 1000)
    return () => clearInterval(ref.current)
  }, [seconds])

  const pct = remaining / seconds
  const isWarning = remaining <= warning
  const mm = Math.floor(remaining / 60).toString().padStart(2, '0')
  const ss = (remaining % 60).toString().padStart(2, '0')

  return (
    <div className={`flex items-center gap-2 px-4 py-2 rounded-xl font-mono text-sm font-bold transition-colors ${
      isWarning ? 'bg-red-600/20 text-red-400 animate-pulse' : 'bg-gray-800 text-white'
    }`}>
      <Clock size={14} />
      {mm}:{ss}
    </div>
  )
}

// ── Result page ────────────────────────────────────────
function ResultPage({ result, onRetry, onHome }) {
  const [expanded, setExpanded] = useState(null)
  const gradeColor = result.percentage >= 80 ? 'text-emerald-400' : result.percentage >= 60 ? 'text-amber-400' : 'text-red-400'

  return (
    <div className="p-6 max-w-3xl mx-auto">
      {/* Score card */}
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8 text-center mb-6">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-indigo-600/20 mb-4">
          <Trophy size={28} className="text-indigo-400" />
        </div>
        <p className={`text-6xl font-black mb-1 ${gradeColor}`}>{result.grade}</p>
        <p className="text-gray-400 text-sm mb-4">{result.percentage}% · {result.total_score}/{result.max_score} points</p>
        <div className="grid grid-cols-3 gap-4 mt-4">
          <div className="bg-gray-800 rounded-xl p-3">
            <p className="text-lg font-bold text-white">{result.question_results.filter(r => r.is_correct).length}</p>
            <p className="text-xs text-gray-400">Correct</p>
          </div>
          <div className="bg-gray-800 rounded-xl p-3">
            <p className="text-lg font-bold text-white">{result.question_results.filter(r => !r.is_correct).length}</p>
            <p className="text-xs text-gray-400">Wrong</p>
          </div>
          <div className="bg-gray-800 rounded-xl p-3">
            <p className="text-lg font-bold text-white">{Math.floor(result.time_taken_seconds / 60)}m {result.time_taken_seconds % 60}s</p>
            <p className="text-xs text-gray-400">Time</p>
          </div>
        </div>
      </div>

      {/* Strengths & weaknesses */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <p className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-2">Strengths</p>
          {result.strengths?.map((s, i) => (
            <p key={i} className="text-xs text-gray-300 flex items-start gap-2 mb-1.5">
              <CheckCircle size={11} className="text-emerald-400 mt-0.5 shrink-0" />{s}
            </p>
          ))}
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <p className="text-xs font-semibold text-amber-400 uppercase tracking-wider mb-2">Needs Work</p>
          {result.weaknesses?.map((s, i) => (
            <p key={i} className="text-xs text-gray-300 flex items-start gap-2 mb-1.5">
              <AlertTriangle size={11} className="text-amber-400 mt-0.5 shrink-0" />{s}
            </p>
          ))}
        </div>
      </div>

      {result.recommendation && (
        <div className="bg-indigo-600/10 border border-indigo-500/30 rounded-xl p-4 mb-6">
          <p className="text-xs text-indigo-400 font-semibold mb-1">Recommendation</p>
          <p className="text-sm text-gray-300">{result.recommendation}</p>
        </div>
      )}

      {/* Question review */}
      <div className="space-y-3 mb-6">
        <p className="text-sm font-semibold text-white">Question Review</p>
        {result.question_results.map((r, i) => (
          <div key={i} className={`bg-gray-900 border rounded-xl overflow-hidden ${r.is_correct ? 'border-emerald-500/30' : 'border-red-500/30'}`}>
            <button onClick={() => setExpanded(expanded === i ? null : i)}
              className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-800/50 transition-colors">
              {r.is_correct
                ? <CheckCircle size={15} className="text-emerald-400 shrink-0" />
                : <XCircle size={15} className="text-red-400 shrink-0" />
              }
              <p className="text-sm text-gray-200 flex-1 truncate">Q{i + 1}. {r.question}</p>
              <span className="text-xs text-gray-500 shrink-0">{r.points_earned}/{r.points_possible}pt</span>
              <ChevronRight size={14} className={`text-gray-500 shrink-0 transition-transform ${expanded === i ? 'rotate-90' : ''}`} />
            </button>
            {expanded === i && (
              <div className="px-4 pb-4 space-y-2 border-t border-gray-800 pt-3">
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-gray-800 rounded-lg p-2.5">
                    <p className="text-xs text-gray-400 mb-1">Your answer</p>
                    <p className="text-xs text-white">{r.your_answer}</p>
                  </div>
                  <div className="bg-gray-800 rounded-lg p-2.5">
                    <p className="text-xs text-gray-400 mb-1">Correct answer</p>
                    <p className="text-xs text-emerald-400">{r.correct_answer}</p>
                  </div>
                </div>
                {r.ai_feedback && (
                  <p className="text-xs text-indigo-300 bg-indigo-600/10 rounded-lg p-2.5">{r.ai_feedback}</p>
                )}
                {r.explanation && (
                  <p className="text-xs text-gray-400 italic">{r.explanation}</p>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="flex gap-3">
        <button onClick={onHome} className="flex-1 px-4 py-2.5 bg-gray-800 hover:bg-gray-700 text-white rounded-xl text-sm font-medium transition-colors">
          Dashboard
        </button>
        <button onClick={onRetry} className="flex-1 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-medium transition-colors flex items-center justify-center gap-2">
          <RotateCcw size={14} />Try Again
        </button>
      </div>
    </div>
  )
}

// ── Main page ──────────────────────────────────────────
export default function MockExamPage() {
  const { user } = useAuthStore()
  const navigate = useNavigate()

  const [phase, setPhase] = useState('setup')   // setup | exam | submitting | result
  const [config, setConfig] = useState({
    topic: 'arrays',
    role: user?.target_role || 'software_engineer',
    difficulty: 'medium',
    num_questions: 10,
    question_types: ['mcq', 'short_answer'],
    timer_mode: 'fixed',
    time_limit_minutes: 20,
    time_per_question_seconds: 90,
  })

  const [examData, setExamData] = useState(null)       // questions + exam_id
  const [answers, setAnswers] = useState({})            // { questionId: answer }
  const [currentIdx, setCurrentIdx] = useState(0)
  const [result, setResult] = useState(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [startTime, setStartTime] = useState(null)
  const [timerKey, setTimerKey] = useState(0)

  const toggleType = (type) => {
    const types = config.question_types
    if (types.includes(type)) {
      if (types.length === 1) return  // keep at least one
      setConfig({ ...config, question_types: types.filter(t => t !== type) })
    } else {
      setConfig({ ...config, question_types: [...types, type] })
    }
  }

  const startExam = async () => {
    setIsGenerating(true)
    try {
      const { data } = await examAPI.start(config)
      setExamData(data)
      setAnswers({})
      setCurrentIdx(0)
      setStartTime(Date.now())
      setTimerKey(k => k + 1)
      setPhase('exam')
    } catch {
      toast.error('Failed to generate exam. Try again.')
    } finally {
      setIsGenerating(false)
    }
  }

  const submitExam = useCallback(async (forcedAnswers) => {
    if (phase === 'submitting' || phase === 'result') return
    setPhase('submitting')
    const finalAnswers = forcedAnswers || answers
    const timeTaken = startTime ? Math.floor((Date.now() - startTime) / 1000) : 0

    try {
      const { data } = await examAPI.submit({
        exam_id: examData.exam_id,
        answers: examData.questions.map((_, i) => ({
          question_id: i,
          answer: finalAnswers[i] || '',
        })),
        total_time_seconds: timeTaken,
      })
      setResult(data)
      setPhase('result')
    } catch {
      toast.error('Failed to submit exam.')
      setPhase('exam')
    }
  }, [phase, answers, examData, startTime])

  const currentQ = examData?.questions?.[currentIdx]
  const answered = Object.keys(answers).length
  const total = examData?.questions?.length || 0

  const handleAnswer = (val) => setAnswers(a => ({ ...a, [currentIdx]: val }))

  const retry = () => {
    setPhase('setup'); setExamData(null); setAnswers({})
    setCurrentIdx(0); setResult(null)
  }

  // ── Setup ──────────────────────────────────────────
  if (phase === 'setup') return (
    <div className="p-8 max-w-2xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Mock Exam</h1>
        <p className="text-gray-400 mt-1">AI-generated timed exam with instant grading</p>
      </div>
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 space-y-5">

        {/* Topic */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Topic</label>
          <select value={config.topic} onChange={e => setConfig({ ...config, topic: e.target.value })}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500">
            {Object.entries(groupedTopics).map(([group, topics]) => (
              <optgroup key={group} label={group}>
                {topics.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
              </optgroup>
            ))}
          </select>
        </div>

        {/* Role */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Role</label>
          <select value={config.role} onChange={e => setConfig({ ...config, role: e.target.value })}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500">
            {Object.entries(groupedRoles).map(([group, roles]) => (
              <optgroup key={group} label={group}>
                {roles.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
              </optgroup>
            ))}
          </select>
        </div>

        {/* Difficulty */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Difficulty</label>
          <div className="flex gap-3">
            {DIFFICULTIES.map(d => (
              <button key={d} onClick={() => setConfig({ ...config, difficulty: d })}
                className={`flex-1 py-2 rounded-lg text-sm font-medium capitalize transition-all ${config.difficulty === d ? 'bg-indigo-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'}`}>
                {d}
              </button>
            ))}
          </div>
        </div>

        {/* Question types */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Question Types</label>
          <div className="flex gap-3">
            {Q_TYPES.map(t => (
              <button key={t.value} onClick={() => toggleType(t.value)}
                className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all ${config.question_types.includes(t.value) ? 'bg-indigo-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'}`}>
                {t.label}
              </button>
            ))}
          </div>
        </div>

        {/* Number of questions */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Number of Questions — <span className="text-indigo-400">{config.num_questions}</span>
          </label>
          <input type="range" min={3} max={30} value={config.num_questions}
            onChange={e => setConfig({ ...config, num_questions: parseInt(e.target.value) })}
            className="w-full accent-indigo-500" />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>3</span><span>30</span>
          </div>
        </div>

        {/* Timer mode */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Timer Mode</label>
          <div className="grid grid-cols-2 gap-3">
            <button onClick={() => setConfig({ ...config, timer_mode: 'fixed' })}
              className={`p-3 rounded-xl border text-left transition-all ${config.timer_mode === 'fixed' ? 'border-indigo-500 bg-indigo-600/10' : 'border-gray-700 hover:border-gray-600'}`}>
              <p className="text-sm font-medium text-white">Fixed Total</p>
              <p className="text-xs text-gray-400 mt-0.5">One timer for entire exam</p>
            </button>
            <button onClick={() => setConfig({ ...config, timer_mode: 'per_question' })}
              className={`p-3 rounded-xl border text-left transition-all ${config.timer_mode === 'per_question' ? 'border-indigo-500 bg-indigo-600/10' : 'border-gray-700 hover:border-gray-600'}`}>
              <p className="text-sm font-medium text-white">Per Question</p>
              <p className="text-xs text-gray-400 mt-0.5">Timer resets each question</p>
            </button>
          </div>
        </div>

        {/* Time config */}
        {config.timer_mode === 'fixed' ? (
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Total Time — <span className="text-indigo-400">{config.time_limit_minutes} min</span>
            </label>
            <input type="range" min={5} max={120} step={5} value={config.time_limit_minutes}
              onChange={e => setConfig({ ...config, time_limit_minutes: parseInt(e.target.value) })}
              className="w-full accent-indigo-500" />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>5 min</span><span>120 min</span>
            </div>
          </div>
        ) : (
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Time per Question — <span className="text-indigo-400">{config.time_per_question_seconds}s</span>
            </label>
            <input type="range" min={30} max={300} step={15} value={config.time_per_question_seconds}
              onChange={e => setConfig({ ...config, time_per_question_seconds: parseInt(e.target.value) })}
              className="w-full accent-indigo-500" />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>30s</span><span>300s</span>
            </div>
          </div>
        )}

        <button onClick={startExam} disabled={isGenerating}
          className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold py-3 rounded-xl transition-colors flex items-center justify-center gap-2">
          {isGenerating ? <Loader2 size={18} className="animate-spin" /> : <BookOpen size={18} />}
          {isGenerating ? `Generating ${config.num_questions} questions...` : 'Start Exam'}
        </button>
      </div>
    </div>
  )

  // ── Submitting ─────────────────────────────────────
  if (phase === 'submitting') return (
    <div className="flex-1 flex items-center justify-center h-full">
      <div className="text-center">
        <Loader2 size={40} className="text-indigo-400 animate-spin mx-auto mb-4" />
        <p className="text-white font-medium">Grading your exam...</p>
        <p className="text-gray-400 text-sm mt-1">AI is evaluating your answers</p>
      </div>
    </div>
  )

  // ── Result ─────────────────────────────────────────
  if (phase === 'result') return (
    <ResultPage result={result} onRetry={retry} onHome={() => navigate('/')} />
  )

  // ── Exam ───────────────────────────────────────────
  if (!currentQ) return null

  const timerSeconds = config.timer_mode === 'fixed'
    ? config.time_limit_minutes * 60
    : config.time_per_question_seconds

  const warningSeconds = config.timer_mode === 'fixed'
    ? config.time_limit_minutes * 60 * 0.2
    : config.time_per_question_seconds * 0.25

  return (
    <div className="flex flex-col h-full">
      {/* Exam top bar */}
      <div className="px-6 py-3 border-b border-gray-800 bg-gray-900 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <p className="text-sm font-medium text-white">
            Q{currentIdx + 1} <span className="text-gray-500">/ {total}</span>
          </p>
          <div className="flex gap-1">
            {examData.questions.map((_, i) => (
              <button key={i} onClick={() => setCurrentIdx(i)}
                className={`w-5 h-5 rounded text-xs font-medium transition-colors ${
                  i === currentIdx ? 'bg-indigo-600 text-white' :
                  answers[i] ? 'bg-emerald-600/30 text-emerald-400' :
                  'bg-gray-800 text-gray-500 hover:bg-gray-700'
                }`}>
                {i + 1}
              </button>
            ))}
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-500">{answered}/{total} answered</span>
          <Timer
            key={config.timer_mode === 'per_question' ? `${timerKey}-${currentIdx}` : timerKey}
            seconds={timerSeconds}
            warning={warningSeconds}
            onExpire={() => {
              if (config.timer_mode === 'per_question') {
                if (currentIdx < total - 1) setCurrentIdx(i => i + 1)
                else submitExam(answers)
              } else {
                submitExam(answers)
              }
            }}
          />
        </div>
      </div>

      {/* Question area */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-2xl mx-auto space-y-5">
          {/* Type badge */}
          <div className="flex items-center gap-2">
            <span className={`text-xs font-semibold px-2.5 py-1 rounded-full uppercase tracking-wider ${
              currentQ.type === 'mcq' ? 'bg-blue-500/20 text-blue-400' :
              currentQ.type === 'coding' ? 'bg-purple-500/20 text-purple-400' :
              'bg-amber-500/20 text-amber-400'
            }`}>
              {currentQ.type.replace('_', ' ')}
            </span>
            <span className="text-xs text-gray-500">{currentQ.points} pt{currentQ.points > 1 ? 's' : ''}</span>
          </div>

          {/* Question */}
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
            <p className="text-sm text-gray-200 leading-relaxed whitespace-pre-wrap">{currentQ.question}</p>
          </div>

          {/* Answer input */}
          {currentQ.type === 'mcq' && currentQ.options && (
            <div className="space-y-2">
              {currentQ.options.map((opt, i) => {
                const letter = opt.split('.')[0].trim()
                const isSelected = answers[currentIdx] === letter
                return (
                  <button key={i} onClick={() => handleAnswer(letter)}
                    className={`w-full text-left px-4 py-3 rounded-xl border text-sm transition-all ${
                      isSelected ? 'border-indigo-500 bg-indigo-600/10 text-white' : 'border-gray-700 text-gray-300 hover:border-gray-600 hover:bg-gray-800'
                    }`}>
                    {opt}
                  </button>
                )
              })}
            </div>
          )}

          {currentQ.type === 'short_answer' && (
            <textarea
              value={answers[currentIdx] || ''}
              onChange={e => handleAnswer(e.target.value)}
              placeholder="Type your answer here..."
              rows={5}
              className="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 resize-none transition-colors"
            />
          )}

          {currentQ.type === 'coding' && (
            <textarea
              value={answers[currentIdx] || ''}
              onChange={e => handleAnswer(e.target.value)}
              placeholder="# Write your code here..."
              rows={10}
              className="w-full bg-gray-950 border border-gray-700 rounded-xl px-4 py-3 text-sm text-gray-200 font-mono placeholder-gray-600 focus:outline-none focus:border-purple-500 resize-none transition-colors"
              style={{ tabSize: 2 }}
              onKeyDown={e => {
                if (e.key === 'Tab') {
                  e.preventDefault()
                  const s = e.target.selectionStart
                  const val = answers[currentIdx] || ''
                  handleAnswer(val.substring(0, s) + '  ' + val.substring(e.target.selectionEnd))
                  setTimeout(() => e.target.setSelectionRange(s + 2, s + 2), 0)
                }
              }}
            />
          )}
        </div>
      </div>

      {/* Bottom nav */}
      <div className="px-6 py-4 border-t border-gray-800 bg-gray-900 flex items-center justify-between">
        <button onClick={() => setCurrentIdx(i => Math.max(0, i - 1))} disabled={currentIdx === 0}
          className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 disabled:opacity-30 text-white rounded-xl text-sm transition-colors">
          <ChevronLeft size={15} />Previous
        </button>

        <button onClick={() => submitExam(answers)}
          className="flex items-center gap-2 px-5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-sm font-medium transition-colors">
          <Send size={14} />Submit Exam
        </button>

        {currentIdx < total - 1 ? (
          <button onClick={() => setCurrentIdx(i => i + 1)}
            className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-xl text-sm transition-colors">
            Next<ChevronRight size={15} />
          </button>
        ) : (
          <div className="w-24" />
        )}
      </div>
    </div>
  )
}