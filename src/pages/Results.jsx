import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import emailjs from '@emailjs/browser'
import { useQuiz } from '../context/QuizContext.jsx'
import { calcScore } from '../context/QuizContext.jsx'
import { useLocalStorage } from '../hooks/useLocalStorage.js'
import ReviewCard from '../components/ReviewCard.jsx'
import { supabase } from '../lib/supabase.js'
import { buildReportPDF, buildReportText } from '../lib/generateReport.js'

function formatDuration(rawMs) {
  const ms  = Math.max(0, rawMs)
  const s   = Math.floor(ms / 1000)
  const h   = Math.floor(s / 3600)
  const m   = Math.floor((s % 3600) / 60)
  const sec = s % 60
  if (h > 0) return `${h}h ${m}m`
  if (m > 0) return `${m}m ${sec}s`
  return `${sec}s`
}

export default function Results() {
  const navigate = useNavigate()
  const {
    questions, answers, startTime, quizComplete, mode,
    dispatch,
  } = useQuiz()

  const [attempts, setAttempts] = useLocalStorage('neet_attempts', [])
  const [emailStatus, setEmailStatus] = useState(null) // null | 'sending' | 'sent' | 'error'

  // Guard: must arrive here with a completed session
  useEffect(() => {
    if (!quizComplete || questions.length === 0) navigate('/', { replace: true })
  }, [quizComplete, questions.length, navigate])

  const score    = useMemo(() => calcScore(answers, questions), [answers, questions])
  const duration = startTime ? Math.max(0, Date.now() - startTime) : 0

  // Write attempt to localStorage and Supabase exactly once on mount.
  // Keying on startTime prevents double-writes in StrictMode.
  useEffect(() => {
    if (!quizComplete || questions.length === 0 || !startTime) return

    setAttempts(prev => {
      if (prev.some(a => a.startTime === startTime)) return prev
      return [
        ...prev,
        {
          date:      new Date().toISOString(),
          startTime,
          score:     score.total,
          total:     questions.length,
          mode,
        },
      ]
    })

    const years = [...new Set(questions.map(q => q.year).filter(Boolean))]
    const year  = years.length === 1 ? years[0] : null

    supabase.from('attempts').insert({
      year,
      score:            score.total,
      max_score:        score.maxScore,
      correct:          score.correct,
      wrong:            score.wrong,
      unanswered:       score.unanswered,
      total_questions:  questions.length,
      mode,
      duration_seconds: Math.round(duration / 1000),
      subject_breakdown: score.bySubject,
    }).then(({ error }) => {
      if (error) console.error('Supabase insert failed:', error.message)
    })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []) // intentionally empty — run once on mount only

  if (!quizComplete || questions.length === 0) return null

  const pct      = score.maxScore > 0 ? Math.round((score.total / score.maxScore) * 100) : 0
  const pctColor = pct >= 60 ? 'text-green-600' : pct >= 40 ? 'text-yellow-600' : 'text-red-600'

  function handleReset() {
    dispatch({ type: 'RESET_QUIZ' })
    navigate('/')
  }

  function handleRetry() {
    dispatch({ type: 'RESET_QUIZ' })
    navigate('/config')
  }

  function handleDownloadPDF() {
    const doc = buildReportPDF({ questions, answers, score, duration, mode, startTime })
    const date = new Date().toISOString().slice(0, 10)
    doc.save(`neet-report-${date}.pdf`)
  }

  async function handleEmailReport() {
    setEmailStatus('sending')
    try {
      const body = buildReportText({ questions, answers, score, duration, mode, startTime })
      const pct  = score.maxScore > 0 ? Math.round((score.total / score.maxScore) * 100) : 0
      const date = startTime
        ? new Date(startTime).toLocaleDateString('en-IN', { dateStyle: 'long' })
        : new Date().toLocaleDateString('en-IN', { dateStyle: 'long' })

      await emailjs.send(
        import.meta.env.VITE_EMAILJS_SERVICE_ID,
        import.meta.env.VITE_EMAILJS_TEMPLATE_ID,
        {
          date,
          mode,
          score:     `${score.total} / ${score.maxScore}`,
          pct:       `${pct}%`,
          correct:   score.correct,
          wrong:     score.wrong,
          unanswered: score.unanswered,
          report_body: body,
        },
        import.meta.env.VITE_EMAILJS_PUBLIC_KEY,
      )
      setEmailStatus('sent')
    } catch (err) {
      console.error('EmailJS error:', err)
      setEmailStatus('error')
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-2xl mx-auto space-y-6">

        {/* ── Score summary ── */}
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 space-y-5">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {score.total}
                <span className="text-gray-400 font-normal text-lg"> / {score.maxScore}</span>
              </h1>
              <p className={`text-lg font-semibold mt-0.5 ${pctColor}`}>{pct}%</p>
            </div>
            <div className="text-right text-sm text-gray-400 space-y-0.5">
              {duration > 0 && <p>{formatDuration(duration)}</p>}
              <p className="capitalize">{mode} · {questions.length}q</p>
            </div>
          </div>

          {/* Counts row */}
          <div className={`grid gap-2 text-center ${score.canceled > 0 ? 'grid-cols-4' : 'grid-cols-3'}`}>
            <CountChip n={score.correct}    label="Correct"  color="green" />
            <CountChip n={score.wrong}      label="Wrong"    color="red"   />
            <CountChip n={score.unanswered} label="Skipped"  color="gray"  />
            {score.canceled > 0 && (
              <CountChip n={score.canceled} label="Canceled" color="yellow" />
            )}
          </div>

          {/* Subject breakdown */}
          <table className="w-full text-sm border-t border-gray-100 pt-4">
            <thead>
              <tr className="text-xs text-gray-400 uppercase">
                <th className="text-left py-1.5">Subject</th>
                <th className="text-center py-1.5">✓</th>
                <th className="text-center py-1.5">✗</th>
                <th className="text-center py-1.5">–</th>
                <th className="text-right py-1.5">Score</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(score.bySubject)
                .filter(([, s]) => s.correct + s.wrong + s.unanswered + s.canceled > 0)
                .map(([subj, s]) => (
                  <tr key={subj} className="border-t border-gray-50">
                    <td className="py-1.5 text-gray-700 font-medium">{subj}</td>
                    <td className="text-center py-1.5 text-green-600">{s.correct}</td>
                    <td className="text-center py-1.5 text-red-500">{s.wrong}</td>
                    <td className="text-center py-1.5 text-gray-400">{s.unanswered}</td>
                    <td className="text-right py-1.5 font-semibold text-gray-800">
                      {s.total} / {s.maxScore}
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>

          {/* Actions */}
          <div className="flex gap-3 pt-1 flex-wrap">
            <button
              onClick={handleReset}
              className="flex-1 py-2 border border-gray-300 rounded-xl text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Home
            </button>
            <button
              onClick={handleRetry}
              className="flex-1 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-semibold transition-colors"
            >
              New quiz
            </button>
          </div>

          <div className="flex gap-3 flex-wrap">
            <button
              onClick={handleDownloadPDF}
              className="flex-1 py-2 border border-gray-300 rounded-xl text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Download PDF
            </button>
            <button
              onClick={handleEmailReport}
              disabled={emailStatus === 'sending' || emailStatus === 'sent'}
              className="flex-1 py-2 border border-indigo-300 rounded-xl text-sm font-medium text-indigo-700 hover:bg-indigo-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {emailStatus === 'sending' ? 'Sending…'
                : emailStatus === 'sent'  ? 'Sent!'
                : emailStatus === 'error' ? 'Failed — retry'
                : 'Email report'}
            </button>
          </div>
        </div>

        {/* ── Review ── */}
        <div>
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
            Review — {questions.length} questions
          </h2>
          <div className="space-y-2">
            {questions.map((q, i) => (
              <ReviewCard
                key={q.id}
                question={q}
                index={i}
                userAnswer={answers[q.id] ?? null}
              />
            ))}
          </div>
        </div>

      </div>
    </div>
  )
}

function CountChip({ n, label, color }) {
  const colors = {
    green:  'bg-green-50  text-green-700',
    red:    'bg-red-50    text-red-600',
    gray:   'bg-gray-100  text-gray-500',
    yellow: 'bg-yellow-50 text-yellow-700',
  }
  return (
    <div className={`rounded-xl p-2 ${colors[color]}`}>
      <div className="text-xl font-bold">{n}</div>
      <div className="text-xs mt-0.5">{label}</div>
    </div>
  )
}
