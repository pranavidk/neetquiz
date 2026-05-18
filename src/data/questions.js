import raw from '../../public/questions.json'

// ─── Primary export ──────────────────────────────────────────────────────────

export const questions = raw

// ─── Fast lookup by year ─────────────────────────────────────────────────────

export const questionsByYear = raw.reduce((acc, q) => {
  ;(acc[q.year] ??= []).push(q)
  return acc
}, {})

// ─── Pre-computed metadata ───────────────────────────────────────────────────
// Computed once at module load; safe to reference in any component without
// wrapping in useMemo.

const years = Object.keys(questionsByYear).map(Number).sort((a, b) => a - b)

const subjects = [...new Set(raw.map(q => q.subject))].sort()

const topics = [...new Set(raw.map(q => q.topic).filter(Boolean))].sort()

// difficulty is not present in the current schema; counts will be 0 unless
// a future extraction pass adds the field.
const difficultyCounts = raw.reduce(
  (acc, q) => {
    const d = q.difficulty
    if (d === 'easy' || d === 'medium' || d === 'hard') acc[d]++
    return acc
  },
  { easy: 0, medium: 0, hard: 0 },
)

export const metadata = {
  totalCount: raw.length,
  years,
  subjects,
  topics,
  difficultyCounts,
}
