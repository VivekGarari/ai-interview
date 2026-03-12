import { useState, useEffect } from 'react'
import { Code2, Play, Loader2, CheckCircle, XCircle, Lightbulb, RefreshCw, ChevronDown, ChevronUp } from 'lucide-react'
import toast from 'react-hot-toast'
import { codingAPI } from '../services/api'
import useAuthStore from '../store/authStore'

const TOPICS = ['arrays', 'strings', 'linked lists', 'trees', 'graphs', 'dynamic programming', 'sorting', 'binary search', 'recursion', 'hashing']
const DIFFICULTIES = ['easy', 'medium', 'hard']
const LANGUAGES = ['python', 'javascript', 'java', 'cpp']

const DEFAULT_CODE = {
  python: '# Write your solution here\n\ndef solution():\n    pass\n',
  javascript: '// Write your solution here\n\nfunction solution() {\n    \n}\n',
  java: '// Write your solution here\n\npublic class Solution {\n    public static void main(String[] args) {\n        \n    }\n}\n',
  cpp: '// Write your solution here\n\n#include <iostream>\nusing namespace std;\n\nint main() {\n    \n    return 0;\n}\n',
}

function DifficultyBadge({ difficulty }) {
  const colors = {
    easy: 'text-emerald-400 bg-emerald-400/10',
    medium: 'text-amber-400 bg-amber-400/10',
    hard: 'text-red-400 bg-red-400/10',
  }
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full capitalize ${colors[difficulty] || colors.medium}`}>
      {difficulty}
    </span>
  )
}

export default function CodingPage() {
  const { user } = useAuthStore()
  const [problem, setProblem] = useState(null)
  const [code, setCode] = useState(DEFAULT_CODE.python)
  const [language, setLanguage] = useState('python')
  const [isGenerating, setIsGenerating] = useState(false)
  const [isRunning, setIsRunning] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [runResult, setRunResult] = useState(null)
  const [submission, setSubmission] = useState(null)
  const [showHint, setShowHint] = useState(false)
  const [showReview, setShowReview] = useState(false)
  const [config, setConfig] = useState({
    difficulty: 'medium',
    topic: 'arrays',
  })

  const generateProblem = async () => {
    setIsGenerating(true)
    setRunResult(null)
    setSubmission(null)
    setShowHint(false)
    setShowReview(false)
    try {
      const { data } = await codingAPI.generate(config)
      setProblem(data)
      setCode(DEFAULT_CODE[language])
    } catch {
      toast.error('Failed to generate problem')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleLanguageChange = (lang) => {
    setLanguage(lang)
    setCode(DEFAULT_CODE[lang])
    setRunResult(null)
  }

  const runCode = async () => {
    if (!code.trim()) return
    setIsRunning(true)
    setRunResult(null)
    try {
      const { data } = await codingAPI.run({ code, language })
      setRunResult(data)
    } catch {
      toast.error('Failed to run code')
    } finally {
      setIsRunning(false)
    }
  }

  const submitCode = async () => {
    if (!problem || !code.trim()) return
    setIsSubmitting(true)
    try {
      const { data } = await codingAPI.submit({ problem_id: problem.id, code, language })
      setSubmission(data)
      setShowReview(true)
      toast.success('Code submitted!')
    } catch {
      toast.error('Failed to submit code')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="flex flex-col h-full bg-gray-950">
      {/* Top bar */}
      <div className="px-6 py-3 border-b border-gray-800 bg-gray-900 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Code2 size={18} className="text-purple-400" />
          <span className="font-medium text-white">Coding Challenge</span>
          {problem && <DifficultyBadge difficulty={problem.difficulty} />}
        </div>
        <div className="flex items-center gap-3">
          {/* Topic */}
          <select value={config.topic} onChange={e => setConfig({ ...config, topic: e.target.value })}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-purple-500">
            {TOPICS.map(t => <option key={t} value={t} className="capitalize">{t}</option>)}
          </select>
          {/* Difficulty */}
          <select value={config.difficulty} onChange={e => setConfig({ ...config, difficulty: e.target.value })}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-purple-500">
            {DIFFICULTIES.map(d => <option key={d} value={d} className="capitalize">{d}</option>)}
          </select>
          <button onClick={generateProblem} disabled={isGenerating}
            className="flex items-center gap-2 px-4 py-1.5 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition-colors">
            {isGenerating ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
            {isGenerating ? 'Generating...' : problem ? 'New Problem' : 'Generate Problem'}
          </button>
        </div>
      </div>

      {!problem ? (
        // Empty state
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="w-16 h-16 bg-purple-600/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Code2 size={28} className="text-purple-400" />
            </div>
            <h2 className="text-xl font-bold text-white mb-2">Ready to practice?</h2>
            <p className="text-gray-400 mb-6">Generate an AI coding challenge to get started</p>
            <button onClick={generateProblem} disabled={isGenerating}
              className="flex items-center gap-2 px-6 py-3 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white rounded-xl font-medium transition-colors mx-auto">
              {isGenerating ? <Loader2 size={18} className="animate-spin" /> : <Code2 size={18} />}
              {isGenerating ? 'Generating...' : 'Generate Problem'}
            </button>
          </div>
        </div>
      ) : (
        <div className="flex flex-1 overflow-hidden">
          {/* Left — problem */}
          <div className="w-[42%] border-r border-gray-800 overflow-y-auto p-5 space-y-4">
            {/* Title */}
            <div>
              <div className="flex items-center gap-2 mb-1">
                <h2 className="text-lg font-bold text-white">{problem.title}</h2>
                <DifficultyBadge difficulty={problem.difficulty} />
              </div>
              <span className="text-xs text-gray-500 capitalize">{problem.topic}</span>
            </div>

            {/* Description */}
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">{problem.description}</p>
            </div>

            {/* Examples */}
            {problem.examples && (
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Example</p>
                <div className="space-y-2">
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Input:</p>
                    <code className="text-xs text-emerald-400 bg-gray-800 px-2 py-1 rounded block">{problem.examples.input}</code>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Output:</p>
                    <code className="text-xs text-emerald-400 bg-gray-800 px-2 py-1 rounded block">{problem.examples.output}</code>
                  </div>
                </div>
              </div>
            )}

            {/* Constraints */}
            {problem.constraints && (
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Constraints</p>
                <p className="text-xs text-gray-400">{problem.constraints}</p>
              </div>
            )}

            {/* Hint */}
            {problem.hints?.hint1 && (
              <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
                <button onClick={() => setShowHint(!showHint)}
                  className="w-full flex items-center justify-between px-4 py-3 text-sm font-medium text-amber-400 hover:bg-gray-800 transition-colors">
                  <div className="flex items-center gap-2">
                    <Lightbulb size={14} />Hint
                  </div>
                  {showHint ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                </button>
                {showHint && (
                  <div className="px-4 pb-3">
                    <p className="text-xs text-gray-300">{problem.hints.hint1}</p>
                  </div>
                )}
              </div>
            )}

            {/* AI Review */}
            {submission && (
              <div className={`bg-gray-900 border rounded-xl overflow-hidden ${submission.code_quality_score >= 7 ? 'border-emerald-500/30' : 'border-amber-500/30'}`}>
                <button onClick={() => setShowReview(!showReview)}
                  className="w-full flex items-center justify-between px-4 py-3 text-sm font-medium text-white hover:bg-gray-800 transition-colors">
                  <div className="flex items-center gap-2">
                    {submission.code_quality_score >= 7
                      ? <CheckCircle size={14} className="text-emerald-400" />
                      : <XCircle size={14} className="text-amber-400" />
                    }
                    AI Review — {submission.code_quality_score}/10
                  </div>
                  {showReview ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                </button>
                {showReview && (
                  <div className="px-4 pb-4 space-y-2">
                    <p className="text-xs text-gray-300">{submission.ai_review}</p>
                    <div className="flex gap-3 text-xs text-gray-400 mt-2">
                      <span className="px-2 py-1 bg-gray-800 rounded">Language: {submission.language}</span>
                      {submission.runtime_ms && <span className="px-2 py-1 bg-gray-800 rounded">Runtime: {submission.runtime_ms}ms</span>}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Right — editor + output */}
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* Editor header */}
            <div className="px-4 py-2 border-b border-gray-800 bg-gray-900 flex items-center justify-between">
              <div className="flex gap-1">
                {LANGUAGES.map(lang => (
                  <button key={lang} onClick={() => handleLanguageChange(lang)}
                    className={`px-3 py-1 rounded-lg text-xs font-medium uppercase transition-colors ${language === lang ? 'bg-purple-600 text-white' : 'text-gray-400 hover:text-white hover:bg-gray-800'}`}>
                    {lang}
                  </button>
                ))}
              </div>
              <div className="flex gap-2">
                <button onClick={runCode} disabled={isRunning}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 text-white rounded-lg text-xs font-medium transition-colors">
                  {isRunning ? <Loader2 size={13} className="animate-spin" /> : <Play size={13} />}
                  Run
                </button>
                <button onClick={submitCode} disabled={isSubmitting}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white rounded-lg text-xs font-medium transition-colors">
                  {isSubmitting ? <Loader2 size={13} className="animate-spin" /> : <CheckCircle size={13} />}
                  Submit
                </button>
              </div>
            </div>

            {/* Code editor (textarea) */}
            <textarea
              value={code}
              onChange={e => setCode(e.target.value)}
              spellCheck={false}
              className="flex-1 bg-gray-950 text-gray-200 font-mono text-sm p-4 resize-none focus:outline-none border-b border-gray-800"
              style={{ tabSize: 2 }}
              onKeyDown={e => {
                if (e.key === 'Tab') {
                  e.preventDefault()
                  const start = e.target.selectionStart
                  const end = e.target.selectionEnd
                  const newCode = code.substring(0, start) + '  ' + code.substring(end)
                  setCode(newCode)
                  setTimeout(() => e.target.setSelectionRange(start + 2, start + 2), 0)
                }
              }}
            />

            {/* Output */}
            <div className="h-44 overflow-y-auto bg-gray-900 border-t border-gray-800">
              <div className="px-4 py-2 border-b border-gray-800 flex items-center justify-between">
                <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">Output</p>
                {runResult && (
                  <span className={`text-xs font-medium ${runResult.success ? 'text-emerald-400' : 'text-red-400'}`}>
                    {runResult.success ? '✓ Success' : '✗ Error'}
                    {runResult.runtime_ms ? ` · ${runResult.runtime_ms}ms` : ''}
                  </span>
                )}
              </div>
              <div className="p-4 font-mono text-xs">
                {!runResult && (
                  <p className="text-gray-600">Click Run to execute your code...</p>
                )}
                {runResult?.stdout && (
                  <pre className="text-emerald-400 whitespace-pre-wrap">{runResult.stdout}</pre>
                )}
                {runResult?.stderr && (
                  <pre className="text-red-400 whitespace-pre-wrap">{runResult.stderr}</pre>
                )}
                {runResult && !runResult.stdout && !runResult.stderr && (
                  <p className="text-gray-500">No output</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}