import { useState, useMemo, useEffect, useRef } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { questions, metadata } from '../data/questions.js'
import { useQuiz } from '../context/QuizContext.jsx'

const ALL_YEARS       = metadata.years          // [2016 … 2025]
const ALL_SUBJECTS    = ['Physics', 'Chemistry', 'Biology']
const ALL_DIFFICULTIES = ['easy', 'medium', 'hard']

// ─── Presets ──────────────────────────────────────────────────────────────────

const PRESETS = {
  mock: {
    subjects:     ALL_SUBJECTS,
    years:        ALL_YEARS,
    topic:        '',
    difficulties: ALL_DIFFICULTIES,
    hideDeleted:  true,
    questionCount: 180,
    timerEnabled: true,
    timerMinutes: 180,
    mode: 'mock',
  },
  topicDrill: {
    subjects:     ALL_SUBJECTS,
    years:        ALL_YEARS,
    topic:        '',           // user must pick a topic
    difficulties: ALL_DIFFICULTIES,
    hideDeleted:  true,
    questionCount: 20,
    timerEnabled: false,
    timerMinutes: 60,
    mode: 'practice',
  },
  subjectRevision: {
    subjects:     ['Physics'], // user adjusts subject
    years:        ALL_YEARS,
    topic:        '',
    difficulties: ALL_DIFFICULTIES,
    hideDeleted:  true,
    questionCount: 45,
    timerEnabled: false,
    timerMinutes: 60,
    mode: 'practice',
  },
}

const DEFAULT_FILTERS = {
  subjects:     ALL_SUBJECTS,
  years:        ALL_YEARS,
  topic:        '',
  difficulties: ALL_DIFFICULTIES,
  hideDeleted:  true,
  questionCount: 45,
  timerEnabled: false,
  timerMinutes: 60,
  mode:         'practice',
}

// ─── Shuffle ──────────────────────────────────────────────────────────────────

function shuffle(arr) {
  const a = [...arr]
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]]
  }
  return a
}

// ─── Filtering ────────────────────────────────────────────────────────────────

function applyFilters(filters) {
  return questions.filter(q => {
    if (!filters.subjects.includes(q.subject))                       return false
    if (!filters.years.includes(q.year))                             return false
    if (filters.topic && q.topic !== filters.topic)                  return false
    if (filters.hideDeleted && q.is_deleted_topic)                   return false
    // difficulty only filters if the field exists on the question
    if (q.difficulty && !filters.difficulties.includes(q.difficulty.toLowerCase())) return false
    return true
  })
}

// ─── Component ────────────────────────────────────────────────────────────────

export default function Config() {
  const navigate   = useNavigate()
  const location   = useLocation()
  const { dispatch } = useQuiz()
  const topicRef   = useRef(null)

  const [f, setF] = useState(() => {
    // "Start mock test" from Home passes { state: { mode: 'mock' } }
    if (location.state?.mode === 'mock') return { ...PRESETS.mock }
    return { ...DEFAULT_FILTERS }
  })

  // Available topics scoped to selected subjects
  const availableTopics = useMemo(() => {
    const seen = new Set()
    questions.forEach(q => {
      if (f.subjects.includes(q.subject) && q.topic) seen.add(q.topic)
    })
    return [...seen].sort()
  }, [f.subjects])

  // Clear topic selection when it's no longer in the available list
  useEffect(() => {
    if (f.topic && !availableTopics.includes(f.topic)) {
      setF(prev => ({ ...prev, topic: '' }))
    }
  }, [availableTopics, f.topic])

  const deletedCount = useMemo(() => questions.filter(q => q.is_deleted_topic).length, [])

  // Live filtered pool
  const filtered = useMemo(() => applyFilters(f), [f])
  const poolSize  = filtered.length

  // Cap questionCount if the pool shrank below it
  useEffect(() => {
    if (f.questionCount > poolSize && poolSize > 0) {
      setF(prev => ({ ...prev, questionCount: poolSize }))
    }
  }, [poolSize, f.questionCount])

  // ── Helpers ──

  function patch(delta) { setF(prev => ({ ...prev, ...delta })) }

  function toggleItem(key, value) {
    setF(prev => {
      const arr = prev[key]
      return {
        ...prev,
        [key]: arr.includes(value) ? arr.filter(v => v !== value) : [...arr, value],
      }
    })
  }

  function applyPreset(name) {
    setF({ ...PRESETS[name] })
    if (name === 'topicDrill') {
      // Scroll/focus topic selector so user knows to pick one
      setTimeout(() => topicRef.current?.focus(), 50)
    }
  }

  function handleStart() {
    const sliced = shuffle(filtered).slice(0, f.questionCount)
    dispatch({
      type: 'START_QUIZ',
      payload: {
        questions:  sliced,
        timeLimit:  f.timerEnabled ? f.timerMinutes * 60 : null,
        mode:       f.mode,
      },
    })
    navigate('/quiz')
  }

  const canStart = poolSize > 0

  // ── Render ──

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-lg mx-auto space-y-5">

        {/* Header */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/')}
            className="text-gray-400 hover:text-gray-600 text-sm"
          >
            ← Back
          </button>
          <h1 className="text-xl font-bold text-gray-900">Configure quiz</h1>
        </div>

        {/* Presets */}
        <div className="flex gap-2 flex-wrap">
          <PresetBtn label="Full mock test"     onClick={() => applyPreset('mock')}            active={f.mode === 'mock' && f.questionCount === 180} />
          <PresetBtn label="Topic drill"        onClick={() => applyPreset('topicDrill')}      active={f.questionCount === 20 && !f.timerEnabled && f.mode === 'practice'} />
          <PresetBtn label="Subject revision"   onClick={() => applyPreset('subjectRevision')} active={f.subjects.length === 1 && f.questionCount === 45 && !f.timerEnabled} />
        </div>

        {/* Subjects */}
        <Section title="Subjects">
          <div className="flex gap-2">
            {ALL_SUBJECTS.map(s => (
              <Pill
                key={s}
                label={s}
                active={f.subjects.includes(s)}
                onClick={() => toggleItem('subjects', s)}
                disabled={f.subjects.length === 1 && f.subjects.includes(s)}
              />
            ))}
          </div>
        </Section>

        {/* Years */}
        <Section title="Years">
          <div className="grid grid-cols-5 gap-y-2 gap-x-2">
            {ALL_YEARS.map(y => (
              <label key={y} className="flex items-center gap-1.5 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={f.years.includes(y)}
                  onChange={() => toggleItem('years', y)}
                  className="accent-blue-600 w-3.5 h-3.5"
                />
                <span className="text-sm text-gray-700">{y}</span>
              </label>
            ))}
          </div>
          {f.years.length < ALL_YEARS.length && (
            <button
              onClick={() => patch({ years: ALL_YEARS })}
              className="mt-2 text-xs text-blue-600 hover:underline"
            >
              Select all years
            </button>
          )}
        </Section>

        {/* Topic */}
        <Section title="Topic">
          <select
            ref={topicRef}
            value={f.topic}
            onChange={e => patch({ topic: e.target.value })}
            className="w-full text-sm border border-gray-300 rounded-lg px-3 py-2 bg-white text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All topics</option>
            {availableTopics.map(t => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </Section>

        {/* Difficulty */}
        <Section title="Difficulty" hint="No effect until difficulty data is added to questions.json">
          <div className="flex gap-2">
            {ALL_DIFFICULTIES.map(d => (
              <Pill
                key={d}
                label={d.charAt(0).toUpperCase() + d.slice(1)}
                active={f.difficulties.includes(d)}
                onClick={() => toggleItem('difficulties', d)}
                disabled={f.difficulties.length === 1 && f.difficulties.includes(d)}
              />
            ))}
          </div>
        </Section>

        {/* Deleted syllabus topics */}
        <Section title="Syllabus">
          <label className="flex items-center gap-3 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={f.hideDeleted}
              onChange={e => patch({ hideDeleted: e.target.checked })}
              className="accent-blue-600 w-4 h-4"
            />
            <span className="text-sm text-gray-700">
              Hide deleted syllabus topics
              <span className="ml-1 text-gray-400 text-xs">({deletedCount} questions)</span>
            </span>
          </label>
        </Section>

        {/* Question count */}
        <Section title="Questions">
          <div className="flex items-center gap-3">
            <input
              type="number"
              min={1}
              max={poolSize}
              value={f.questionCount}
              onChange={e => {
                const n = Math.max(1, Math.min(Number(e.target.value), poolSize))
                patch({ questionCount: n })
              }}
              className="w-24 text-sm border border-gray-300 rounded-lg px-3 py-2 text-center focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-400">max {poolSize}</span>
          </div>
        </Section>

        {/* Timer */}
        <Section title="Timer">
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={f.timerEnabled}
                onChange={e => patch({ timerEnabled: e.target.checked })}
                className="accent-blue-600 w-4 h-4"
              />
              <span className="text-sm text-gray-700">Enable timer</span>
            </label>
            {f.timerEnabled && (
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  min={1}
                  max={360}
                  value={f.timerMinutes}
                  onChange={e => patch({ timerMinutes: Math.max(1, Number(e.target.value)) })}
                  className="w-20 text-sm border border-gray-300 rounded-lg px-3 py-2 text-center focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-400">min</span>
              </div>
            )}
          </div>
        </Section>

        {/* Live count + Start */}
        <div className="flex items-center justify-between pt-1">
          <p className={`text-sm ${poolSize === 0 ? 'text-red-500' : 'text-gray-500'}`}>
            {poolSize === 0
              ? 'No questions match your filters'
              : <><span className="font-semibold text-gray-800">{Math.min(f.questionCount, poolSize)}</span> of {poolSize} questions</>
            }
          </p>
          <button
            onClick={handleStart}
            disabled={!canStart}
            className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-semibold rounded-xl transition-colors"
          >
            Start quiz →
          </button>
        </div>

      </div>
    </div>
  )
}

// ─── Small local components ───────────────────────────────────────────────────

function Section({ title, hint, children }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 space-y-3">
      <div className="flex items-baseline gap-2">
        <span className="text-sm font-semibold text-gray-800">{title}</span>
        {hint && <span className="text-xs text-gray-400">{hint}</span>}
      </div>
      {children}
    </div>
  )
}

function Pill({ label, active, onClick, disabled }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`px-4 py-1.5 rounded-full border text-sm font-medium transition-colors
        ${active
          ? 'bg-blue-600 border-blue-600 text-white'
          : 'bg-white border-gray-300 text-gray-700 hover:border-blue-400'}
        ${disabled ? 'opacity-50 cursor-default' : 'cursor-pointer'}`}
    >
      {label}
    </button>
  )
}

function PresetBtn({ label, onClick, active }) {
  return (
    <button
      onClick={onClick}
      className={`px-3 py-1.5 rounded-lg border text-xs font-medium transition-colors
        ${active
          ? 'bg-gray-900 border-gray-900 text-white'
          : 'bg-white border-gray-300 text-gray-600 hover:border-gray-500'}`}
    >
      {label}
    </button>
  )
}
