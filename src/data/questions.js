// Questions are loaded at runtime via fetch (not bundled).
// Use QuestionsContext / useQuestions() in components.

export async function loadQuestions() {
  const res = await fetch(`${import.meta.env.BASE_URL}questions.json`)
  if (!res.ok) throw new Error(`Failed to load questions.json: ${res.status}`)
  return res.json()
}

export function computeMetadata(raw) {
  const byYear = {}
  for (const q of raw) (byYear[q.year] ??= []).push(q)

  // Preserve original types: numeric years stay numbers, "MOCK-N" stays string.
  // Numbers sort before strings so PYQ years come first.
  const years = Object.keys(byYear)
    .map(k => { const n = Number(k); return isNaN(n) ? k : n })
    .sort((a, b) => {
      if (typeof a === 'number' && typeof b === 'number') return a - b
      if (typeof a === 'number') return -1
      if (typeof b === 'number') return 1
      return String(a).localeCompare(String(b))
    })

  const subjects = [...new Set(raw.map(q => q.subject))].sort()
  const topics   = [...new Set(raw.map(q => q.topic).filter(Boolean))].sort()

  const difficultyCounts = raw.reduce(
    (acc, q) => {
      const d = q.difficulty
      if (d === 'easy' || d === 'medium' || d === 'hard') acc[d]++
      return acc
    },
    { easy: 0, medium: 0, hard: 0 },
  )

  return { totalCount: raw.length, years, subjects, topics, difficultyCounts }
}
