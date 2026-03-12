import { useState, useRef, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Video, VideoOff, Volume2, VolumeX,
  Loader2, CheckCircle, ChevronRight, Trophy, RotateCcw,
  Play, Square, AlertCircle, Mic
} from 'lucide-react'
import toast from 'react-hot-toast'
import { videoAPI } from '../services/api'
import useAuthStore from '../store/authStore'

const TYPES = [
  { value: 'behavioral', label: 'Behavioral' },
  { value: 'technical', label: 'Technical' },
  { value: 'system_design', label: 'System Design' },
  { value: 'hr', label: 'HR Round' },
]
const DIFFICULTIES = ['easy', 'medium', 'hard']

function ReportModal({ report, onRestart, onClose }) {
  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-xl p-8 overflow-y-auto max-h-[90vh]">
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-indigo-600/20 mb-4">
            <Trophy size={28} className="text-indigo-400" />
          </div>
          <h2 className="text-2xl font-bold text-white">Video Interview Complete!</h2>
        </div>
        <div className="grid grid-cols-3 gap-4 mb-6">
          {[
            { label: 'Overall', score: report.overall_score },
            { label: 'Content', score: report.content_score },
            { label: 'Communication', score: report.communication_score },
          ].map(({ label, score }) => (
            <div key={label} className="bg-gray-800 rounded-xl p-4 text-center">
              <p className={`text-3xl font-black ${score >= 7 ? 'text-emerald-400' : score >= 5 ? 'text-amber-400' : 'text-red-400'}`}>
                {Math.round(score)}
              </p>
              <p className="text-xs text-gray-400 mt-1">{label}</p>
            </div>
          ))}
        </div>
        <div className="grid grid-cols-3 gap-3 mb-6">
          <div className="bg-gray-800 rounded-xl p-3 text-center">
            <p className="text-xl font-bold text-white">{report.average_wpm}</p>
            <p className="text-xs text-gray-400">WPM</p>
          </div>
          <div className="bg-gray-800 rounded-xl p-3 text-center">
            <p className="text-xl font-bold text-white">{report.total_questions}</p>
            <p className="text-xs text-gray-400">Questions</p>
          </div>
          <div className="bg-gray-800 rounded-xl p-3 text-center">
            <p className="text-xl font-bold text-white">{report.total_filler_words}</p>
            <p className="text-xs text-gray-400">Filler Words</p>
          </div>
        </div>
        <p className="text-gray-300 text-sm leading-relaxed mb-5 text-center">{report.summary}</p>
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
            <RotateCcw size={14} />Try Again
          </button>
        </div>
      </div>
    </div>
  )
}

export default function VideoInterviewPage() {
  const { user } = useAuthStore()
  const navigate = useNavigate()

  const [phase, setPhase] = useState('setup')
  const [config, setConfig] = useState({
    interview_type: 'behavioral',
    target_role: user?.target_role?.replace(/_/g, ' ') || 'software engineer',
    difficulty: 'medium',
  })

  const [session, setSession] = useState(null)
  const [currentQuestion, setCurrentQuestion] = useState(null)
  const [questionsAnswered, setQuestionsAnswered] = useState(0)
  const [feedback, setFeedback] = useState(null)
  const [report, setReport] = useState(null)
  const [cameraOn, setCameraOn] = useState(true)
  const [soundOn, setSoundOn] = useState(true)
  const [isRecording, setIsRecording] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [isPlayingAudio, setIsPlayingAudio] = useState(false)
  const [canRecord, setCanRecord] = useState(false)
  const [recordingTime, setRecordingTime] = useState(0)
  const [status, setStatus] = useState('Starting...')

  // Separate refs for camera and recording
  const videoRef = useRef(null)
  const cameraStreamRef = useRef(null)   // video only — for display
  const mediaRecorderRef = useRef(null)
  const audioChunksRef = useRef([])
  const timerRef = useRef(null)
  const audioRef = useRef(new Audio())
  const questionsAnsweredRef = useRef(0)
  const recordingTimeRef = useRef(0)

  useEffect(() => { questionsAnsweredRef.current = questionsAnswered }, [questionsAnswered])
  useEffect(() => { recordingTimeRef.current = recordingTime }, [recordingTime])

  // Start camera (video only for display)
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false })
      cameraStreamRef.current = stream
      if (videoRef.current) videoRef.current.srcObject = stream
      return true
    } catch {
      toast.error('Camera access denied.')
      setCameraOn(false)
      return false
    }
  }

  const stopCamera = () => {
    cameraStreamRef.current?.getTracks().forEach(t => t.stop())
    cameraStreamRef.current = null
  }

  useEffect(() => {
    return () => {
      stopCamera()
      clearInterval(timerRef.current)
      audioRef.current.pause()
    }
  }, [])

  const toggleCamera = () => {
    const track = cameraStreamRef.current?.getVideoTracks()[0]
    if (track) { track.enabled = !track.enabled; setCameraOn(v => !v) }
  }

  const playQuestionAudio = useCallback((questionId) => {
    setIsPlayingAudio(true)
    setCanRecord(false)
    setStatus('AI interviewer is speaking...')

    if (!soundOn) {
      setTimeout(() => {
        setIsPlayingAudio(false)
        setCanRecord(true)
        setStatus('Your turn — click Record Answer')
      }, 300)
      return
    }

    const url = videoAPI.questionAudioUrl(questionId)
    fetch(url)
      .then(r => r.ok ? r.blob() : Promise.reject())
      .then(blob => {
        const objUrl = URL.createObjectURL(blob)
        const audio = audioRef.current
        audio.src = objUrl
        const done = () => {
          setIsPlayingAudio(false)
          setCanRecord(true)
          setStatus('Your turn — click Record Answer')
          URL.revokeObjectURL(objUrl)
        }
        audio.onended = done
        audio.onerror = done
        audio.play().catch(done)
      })
      .catch(() => {
        setIsPlayingAudio(false)
        setCanRecord(true)
        setStatus('Your turn — click Record Answer')
      })
  }, [soundOn])

  const startSession = async () => {
    setIsProcessing(true)
    try {
      
      const { data } = await videoAPI.start(config)
      setSession(data)
      setCurrentQuestion(data.question)
      setPhase('interview')

      // Wait for video element to mount before attaching stream
      setTimeout(async () => {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false })
        cameraStreamRef.current = stream
        if (videoRef.current) {
          videoRef.current.srcObject = stream
          console.log('Camera attached!')
        } else {
          console.log('Video element still not found')
        }
        playQuestionAudio(data.question.id)
      }, 300)
    } catch {
      toast.error('Failed to start session')
      stopCamera()
    } finally {
      setIsProcessing(false)
    }
  }

  // Recording uses a fresh audio-only stream each time
  const startRecording = async () => {
    if (isRecording || !canRecord) return
    try {
      const audioStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false })
      audioChunksRef.current = []

      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : MediaRecorder.isTypeSupported('audio/webm')
        ? 'audio/webm'
        : ''

      const recorder = new MediaRecorder(audioStream, mimeType ? { mimeType } : {})
      recorder.ondataavailable = e => { if (e.data.size > 0) audioChunksRef.current.push(e.data) }
      recorder.onstop = () => audioStream.getTracks().forEach(t => t.stop())
      recorder.start(100)
      mediaRecorderRef.current = recorder

      setIsRecording(true)
      setCanRecord(false)
      setRecordingTime(0)
      setStatus('Recording... speak your answer')
      timerRef.current = setInterval(() => setRecordingTime(t => t + 1), 1000)
    } catch (err) {
      toast.error('Microphone access failed. Please allow microphone permissions.')
    }
  }

  const stopRecording = () => {
    if (!isRecording) return
    clearInterval(timerRef.current)
    setIsRecording(false)
    setStatus('Processing your answer...')

    const recorder = mediaRecorderRef.current
    recorder.onstop = async () => {
      recorder.stream?.getTracks().forEach(t => t.stop())
      await submitAudio()
    }
    recorder.stop()
  }

  const submitAudio = async () => {
    const chunks = audioChunksRef.current
    if (!chunks.length) {
      toast.error('No audio recorded. Try again.')
      setCanRecord(true)
      setStatus('Your turn — click Record Answer')
      return
    }

    setIsProcessing(true)
    const blob = new Blob(chunks, { type: 'audio/webm' })
    const formData = new FormData()
    formData.append('session_id', session.session_id)
    formData.append('question_id', currentQuestion.id)
    formData.append('duration_seconds', String(recordingTimeRef.current))
    formData.append('audio', blob, 'answer.webm')

    try {
      const { data } = await videoAPI.transcribe(formData)
      setFeedback(data)
      const newCount = questionsAnsweredRef.current + 1
      setQuestionsAnswered(newCount)

      if (data.session_complete || newCount >= 5) {
        setStatus('Generating your report...')
        const { data: rep } = await videoAPI.end(session.session_id)
        setReport(rep)
      } else {
        setCurrentQuestion(data.next_question)
        setStatus('Next question in 3 seconds...')
        setTimeout(() => {
          setFeedback(null)
          playQuestionAudio(data.next_question.id)
        }, 3000)
      }
    } catch {
      toast.error('Failed to process. Please try again.')
      setCanRecord(true)
      setStatus('Your turn — click Record Answer')
    } finally {
      setIsProcessing(false)
    }
  }

  const restart = () => {
    stopCamera()
    clearInterval(timerRef.current)
    audioRef.current.pause()
    setPhase('setup'); setSession(null); setCurrentQuestion(null)
    setQuestionsAnswered(0); setFeedback(null); setReport(null)
    setIsRecording(false); setIsProcessing(false); setIsPlayingAudio(false)
    setCanRecord(false); setRecordingTime(0); setStatus('Starting...')
  }

  const formatTime = s => `${Math.floor(s/60).toString().padStart(2,'0')}:${(s%60).toString().padStart(2,'0')}`

  // ── Setup ─────────────────────────────────────────
  if (phase === 'setup') return (
    <div className="p-8 max-w-2xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Video Interview</h1>
        <p className="text-gray-400 mt-1">Real interview simulation with AI voice + camera</p>
      </div>
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-3">Interview Type</label>
          <div className="grid grid-cols-2 gap-3">
            {TYPES.map(t => (
              <button key={t.value} onClick={() => setConfig({ ...config, interview_type: t.value })}
                className={`p-3 rounded-xl border text-left transition-all ${config.interview_type === t.value ? 'border-indigo-500 bg-indigo-600/10' : 'border-gray-700 hover:border-gray-600'}`}>
                <p className="text-sm font-medium text-white">{t.label}</p>
              </button>
            ))}
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Target Role</label>
          <input value={config.target_role} onChange={e => setConfig({ ...config, target_role: e.target.value })}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 transition-colors"
            placeholder="e.g. Software Engineer" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-3">Difficulty</label>
          <div className="flex gap-3">
            {DIFFICULTIES.map(d => (
              <button key={d} onClick={() => setConfig({ ...config, difficulty: d })}
                className={`flex-1 py-2 rounded-lg text-sm font-medium capitalize transition-all ${config.difficulty === d ? 'bg-indigo-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'}`}>
                {d}
              </button>
            ))}
          </div>
        </div>
        <div className="flex items-start gap-3 p-3 bg-amber-500/10 border border-amber-500/30 rounded-xl">
          <AlertCircle size={16} className="text-amber-400 mt-0.5 shrink-0" />
          <p className="text-xs text-amber-300">Camera and microphone access required. Allow permissions when prompted.</p>
        </div>
        <button onClick={startSession} disabled={isProcessing}
          className="w-full bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white font-semibold py-3 rounded-xl transition-colors flex items-center justify-center gap-2">
          {isProcessing ? <Loader2 size={18} className="animate-spin" /> : <Video size={18} />}
          {isProcessing ? 'Starting...' : 'Start Video Interview'}
        </button>
      </div>
    </div>
  )

  // ── Interview ─────────────────────────────────────
  return (
    <div className="flex flex-col h-full bg-gray-950">
      {/* Top bar */}
      <div className="px-6 py-3 border-b border-gray-800 bg-gray-900 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
          <span className="text-sm font-medium text-white capitalize">{config.interview_type.replace('_', ' ')} Interview</span>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-400">{questionsAnswered}/5</span>
          <div className="w-20 h-1 bg-gray-800 rounded-full overflow-hidden">
            <div className="h-full bg-rose-500 rounded-full transition-all" style={{ width: `${(questionsAnswered/5)*100}%` }} />
          </div>
          <button onClick={restart} className="text-xs text-gray-500 hover:text-red-400 transition-colors">End</button>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Left — camera + controls */}
        <div className="flex flex-col w-[55%] p-4 gap-4">
          {/* Camera feed */}
          <div className="relative flex-1 bg-gray-900 rounded-2xl overflow-hidden border border-gray-800">
            <video ref={videoRef} autoPlay muted playsInline
              className={`w-full h-full object-cover ${!cameraOn ? 'hidden' : ''}`} />
            {!cameraOn && (
              <div className="w-full h-full flex items-center justify-center">
                <div className="w-20 h-20 rounded-full bg-gray-700 flex items-center justify-center text-3xl font-bold text-white">
                  {user?.full_name?.[0]?.toUpperCase()}
                </div>
              </div>
            )}
            {isRecording && (
              <div className="absolute top-3 left-3 flex items-center gap-2 bg-red-600/90 rounded-full px-3 py-1.5">
                <div className="w-2 h-2 rounded-full bg-white animate-pulse" />
                <span className="text-xs text-white font-mono font-bold">{formatTime(recordingTime)}</span>
              </div>
            )}
            <div className="absolute bottom-3 left-3 bg-black/60 rounded-lg px-2 py-1">
              <p className="text-xs text-white">{user?.full_name}</p>
            </div>
          </div>

          {/* AI speaker */}
          <div className="h-24 bg-gray-900 rounded-2xl border border-gray-800 flex items-center gap-4 px-5">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 transition-colors ${isPlayingAudio ? 'bg-indigo-600' : 'bg-gray-700'}`}>
              {isPlayingAudio ? <Volume2 size={18} className="text-white animate-pulse" /> : <Video size={18} className="text-white" />}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white">AI Interviewer</p>
              {isPlayingAudio
                ? <div className="flex gap-0.5 mt-1.5 items-end h-4">
                    {[...Array(8)].map((_, i) => (
                      <div key={i} className="w-1 bg-indigo-400 rounded-full animate-bounce"
                        style={{ height: `${6 + (i % 3) * 4}px`, animationDelay: `${i * 80}ms` }} />
                    ))}
                  </div>
                : <p className="text-xs text-gray-400 truncate mt-0.5">{status}</p>
              }
            </div>
          </div>

          {/* Controls */}
          <div className="flex items-center justify-center gap-3">
            <button onClick={toggleCamera} title="Toggle camera"
              className={`w-10 h-10 rounded-full flex items-center justify-center transition-colors ${cameraOn ? 'bg-gray-700 hover:bg-gray-600' : 'bg-red-600 hover:bg-red-500'}`}>
              {cameraOn ? <Video size={16} className="text-white" /> : <VideoOff size={16} className="text-white" />}
            </button>

            <button onClick={() => setSoundOn(v => !v)} title="Toggle AI voice"
              className={`w-10 h-10 rounded-full flex items-center justify-center transition-colors ${soundOn ? 'bg-gray-700 hover:bg-gray-600' : 'bg-red-600 hover:bg-red-500'}`}>
              {soundOn ? <Volume2 size={16} className="text-white" /> : <VolumeX size={16} className="text-white" />}
            </button>

            {!isRecording ? (
              <button onClick={startRecording} disabled={!canRecord || isProcessing}
                className={`flex items-center gap-2 px-5 py-2.5 rounded-full font-medium text-sm transition-all ${
                  canRecord && !isProcessing
                    ? 'bg-rose-600 hover:bg-rose-500 text-white hover:scale-105'
                    : 'bg-gray-700 text-gray-500 cursor-not-allowed'
                }`}>
                <Mic size={15} />
                {isProcessing ? 'Processing...' : canRecord ? 'Record Answer' : 'Wait...'}
              </button>
            ) : (
              <button onClick={stopRecording}
                className="flex items-center gap-2 px-5 py-2.5 bg-gray-800 border-2 border-red-500 text-red-400 rounded-full font-medium text-sm hover:bg-red-600 hover:text-white hover:border-red-600 transition-all">
                <Square size={15} />Stop Recording
              </button>
            )}
          </div>
        </div>

        {/* Right — question + feedback */}
        <div className="flex-1 p-4 flex flex-col gap-4 overflow-y-auto border-l border-gray-800">
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-6 h-6 rounded-full bg-indigo-600 flex items-center justify-center text-xs font-bold text-white">
                {questionsAnswered + 1}
              </div>
              <p className="text-xs text-gray-400 font-medium uppercase tracking-wider">Question</p>
              {isPlayingAudio && <Volume2 size={12} className="text-indigo-400 animate-pulse ml-auto" />}
            </div>
            <p className="text-sm text-gray-200 leading-relaxed">
              {currentQuestion?.text || currentQuestion?.question_text || 'Loading...'}
            </p>
          </div>

          {isProcessing && !feedback && (
            <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 flex items-center gap-3">
              <Loader2 size={18} className="text-indigo-400 animate-spin shrink-0" />
              <div>
                <p className="text-sm text-white">Analyzing your answer...</p>
                <p className="text-xs text-gray-400 mt-0.5">Transcribing and evaluating</p>
              </div>
            </div>
          )}

          {feedback && (
            <div className="bg-gray-900 border border-gray-700 rounded-2xl p-5 space-y-3">
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Answer Feedback</p>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-gray-800 rounded-xl p-3">
                  <p className="text-xs text-gray-400 mb-1">Content</p>
                  <p className={`text-2xl font-black ${feedback.content_score >= 7 ? 'text-emerald-400' : feedback.content_score >= 5 ? 'text-amber-400' : 'text-red-400'}`}>
                    {feedback.content_score}<span className="text-sm text-gray-500">/10</span>
                  </p>
                </div>
                <div className="bg-gray-800 rounded-xl p-3">
                  <p className="text-xs text-gray-400 mb-1">Communication</p>
                  <p className={`text-2xl font-black ${feedback.communication_score >= 7 ? 'text-emerald-400' : feedback.communication_score >= 5 ? 'text-amber-400' : 'text-red-400'}`}>
                    {feedback.communication_score}<span className="text-sm text-gray-500">/10</span>
                  </p>
                </div>
              </div>
              <p className="text-sm text-gray-300 leading-relaxed">{feedback.content_feedback}</p>
              <div className="flex flex-wrap gap-2 text-xs">
                <span className="px-2 py-1 bg-gray-800 rounded-lg text-gray-300">🎤 {feedback.words_per_minute} WPM</span>
                <span className="px-2 py-1 bg-gray-800 rounded-lg text-gray-300">{feedback.pace_feedback}</span>
              </div>
              {Object.keys(feedback.filler_words_found || {}).length > 0 && (
                <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-3">
                  <p className="text-xs text-amber-400 font-medium mb-1">Filler words detected:</p>
                  <p className="text-xs text-gray-300">{Object.entries(feedback.filler_words_found).map(([w,c]) => `"${w}" ×${c}`).join(', ')}</p>
                </div>
              )}
              {feedback.transcript && (
                <details className="text-xs">
                  <summary className="text-gray-500 cursor-pointer hover:text-gray-300 select-none">View transcript</summary>
                  <p className="mt-2 text-gray-400 leading-relaxed bg-gray-800 rounded-lg p-3">{feedback.transcript}</p>
                </details>
              )}
              <p className="text-xs text-center text-indigo-400 font-medium">
                {feedback.session_complete ? '⏳ Generating final report...' : '⏭ Next question in 3 seconds...'}
              </p>
            </div>
          )}

          {!feedback && !isProcessing && (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <div className={`w-16 h-16 rounded-full mx-auto mb-3 flex items-center justify-center ${canRecord ? 'bg-rose-600/20 border-2 border-rose-500' : 'bg-gray-800'}`}>
                  {isPlayingAudio
                    ? <Volume2 size={24} className="text-indigo-400 animate-pulse" />
                    : canRecord
                      ? <Mic size={24} className="text-rose-400" />
                      : <Loader2 size={24} className="text-gray-500 animate-spin" />
                  }
                </div>
                <p className="text-sm text-gray-400">{status}</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {report && <ReportModal report={report} onRestart={restart} onClose={() => navigate('/history')} />}
    </div>
  )
}