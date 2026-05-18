import { createContext, useContext, useReducer, useMemo } from 'react'

// ─── Scoring ──────────────────────────────────────────────────────────────────
// answers values are 1-indexed (1|2|3|4|null) to match correct_answer in the
// data. null means the user explicitly cleared their selection; undefined means
// the question was never opened. Both count as unanswered (0 pts).

function scoreSubject(qs, answers) {
  let correct = 0, wrong = 0, unanswered = 0, canceled = 0

  for (const q of qs) {
    if (q.correct_answer === null) {
      // NTA-canceled: always 0 regardless of user selection
      canceled++
      continue
    }
    const a = answers[q.id]
    if (a == null) {
      unanswered++
    } else if (a === q.correct_answer) {
      correct++
    } else {
      wrong++
    }
  }

  return {
    correct,
    wrong,
    unanswered,
    canceled,
    total: correct * 4 - wrong,
    maxScore: (qs.length - canceled) * 4,
  }
}

export function calcScore(answers, questions) {
  const overall = scoreSubject(questions, answers)

  const bySubject = {}
  for (const subj of ['Physics', 'Chemistry', 'Biology']) {
    bySubject[subj] = scoreSubject(
      questions.filter(q => q.subject === subj),
      answers,
    )
  }

  return { ...overall, bySubject }
}

// ─── State ────────────────────────────────────────────────────────────────────

const initialState = {
  questions: [],
  currentIndex: 0,
  answers: {},       // { [q.id]: 1|2|3|4|null }
  flagged: new Set(),
  startTime: null,
  timeLimit: null,   // null = untimed, number = seconds
  quizComplete: false,
  mode: 'practice',  // 'practice' | 'mock'
}

// ─── Reducer ──────────────────────────────────────────────────────────────────

function reducer(state, action) {
  switch (action.type) {
    case 'START_QUIZ': {
      const { questions, timeLimit = null, mode = 'practice' } = action.payload
      return {
        ...initialState,
        flagged: new Set(), // never share the same Set reference across sessions
        questions,
        timeLimit,
        mode,
        startTime: Date.now(),
      }
    }

    case 'ANSWER_QUESTION': {
      const { id, optionIndex } = action.payload
      // Passing the same optionIndex that's already selected clears the answer
      const current = state.answers[id]
      const next = current === optionIndex ? null : optionIndex
      return {
        ...state,
        answers: { ...state.answers, [id]: next },
      }
    }

    case 'TOGGLE_FLAG': {
      const next = new Set(state.flagged)
      next.has(action.payload) ? next.delete(action.payload) : next.add(action.payload)
      return { ...state, flagged: next }
    }

    case 'NAVIGATE_TO': {
      const index = Math.max(0, Math.min(action.payload, state.questions.length - 1))
      return { ...state, currentIndex: index }
    }

    case 'COMPLETE_QUIZ':
      return { ...state, quizComplete: true }

    case 'RESET_QUIZ':
      return { ...initialState, flagged: new Set() }

    default:
      return state
  }
}

// ─── Context ──────────────────────────────────────────────────────────────────

const QuizContext = createContext(null)

export function QuizProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState)

  const value = useMemo(() => ({
    // state
    questions:    state.questions,
    currentIndex: state.currentIndex,
    answers:      state.answers,
    flagged:      state.flagged,
    startTime:    state.startTime,
    timeLimit:    state.timeLimit,
    quizComplete: state.quizComplete,
    mode:         state.mode,
    // derived
    currentQuestion: state.questions[state.currentIndex] ?? null,
    answeredCount:   Object.values(state.answers).filter(v => v != null).length,
    unansweredCount: state.questions.length - Object.values(state.answers).filter(v => v != null).length,
    flaggedCount:    state.flagged.size,
    // actions
    dispatch,
  }), [state])

  return <QuizContext.Provider value={value}>{children}</QuizContext.Provider>
}

export function useQuiz() {
  const ctx = useContext(QuizContext)
  if (!ctx) throw new Error('useQuiz must be used within <QuizProvider>')
  return ctx
}
