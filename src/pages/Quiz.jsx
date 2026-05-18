import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuiz } from '../context/QuizContext.jsx'
import QuestionCard from '../components/QuestionCard.jsx'
import QuestionGrid from '../components/QuestionGrid.jsx'
import ProgressBar from '../components/ProgressBar.jsx'
import Timer from '../components/Timer.jsx'

const SUBJECT_COLOR = {
  Physics:   'bg-blue-100 text-blue-700',
  Chemistry: 'bg-green-100 text-green-700',
  Biology:   'bg-purple-100 text-purple-700',
}

export default function Quiz() {
  const navigate = useNavigate()
  const {
    questions, currentIndex, currentQuestion,
    answers, flagged, answeredCount, unansweredCount, flaggedCount,
    startTime, timeLimit, quizComplete,
    dispatch,
  } = useQuiz()

  const [showGrid,    setShowGrid]    = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)

  // No active session → back to home; close any open overlays first so they
  // don't linger visibly during the transition
  useEffect(() => {
    if (questions.length === 0) {
      setShowGrid(false)
      setShowConfirm(false)
      navigate('/', { replace: true })
    }
  }, [questions.length, navigate])

  // Reducer set quizComplete → go to results
  useEffect(() => {
    if (quizComplete) navigate('/results', { replace: true })
  }, [quizComplete, navigate])

  const handleExpire = useCallback(() => {
    dispatch({ type: 'COMPLETE_QUIZ' })
  }, [dispatch])

  const handleConfirmSubmit = useCallback(() => {
    dispatch({ type: 'COMPLETE_QUIZ' })
  }, [dispatch])

  const handleAnswer = useCallback((optionIndex) => {
    if (!currentQuestion) return
    dispatch({ type: 'ANSWER_QUESTION', payload: { id: currentQuestion.id, optionIndex } })
  }, [dispatch, currentQuestion])

  const handleToggleFlag = useCallback(() => {
    if (!currentQuestion) return
    dispatch({ type: 'TOGGLE_FLAG', payload: currentQuestion.id })
  }, [dispatch, currentQuestion])

  const handleNavigate = useCallback((index) => {
    dispatch({ type: 'NAVIGATE_TO', payload: index })
  }, [dispatch])

  if (!currentQuestion) return null

  const isFlagged    = flagged.has(currentQuestion.id)
  const selectedAnswer = answers[currentQuestion.id] ?? null
  const isLast       = currentIndex === questions.length - 1

  // overflow-hidden on the root locks scroll when an overlay is open.
  // All overlays use absolute (not fixed) so they're scoped to this container,
  // avoiding iOS Safari's broken fixed-position-inside-scroll-container behaviour.
  const overlayOpen = showGrid || showConfirm

  return (
    <div
      id="quiz-root"
      className={`relative min-h-screen bg-gray-50 flex flex-col ${overlayOpen ? 'h-screen overflow-hidden' : ''}`}
    >

      {/* ── Top bar ── */}
      <header className="sticky top-0 z-20 bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-5xl mx-auto px-4 h-13 flex items-center gap-3 py-2">

          <span className={`hidden sm:inline-block px-2 py-0.5 rounded text-xs font-semibold ${SUBJECT_COLOR[currentQuestion.subject]}`}>
            {currentQuestion.subject}
          </span>

          <span className="text-sm text-gray-500 flex-shrink-0">
            Q {currentIndex + 1} <span className="text-gray-300">/</span> {questions.length}
          </span>

          <ProgressBar
            value={answeredCount}
            max={questions.length}
            className="flex-1 hidden sm:flex"
          />

          {timeLimit !== null && startTime !== null && (
            <Timer
              timeLimit={timeLimit}
              startTime={startTime}
              onExpire={handleExpire}
            />
          )}

          {/* Grid toggle — mobile only */}
          <button
            onClick={() => setShowGrid(true)}
            className="sm:hidden text-xs border border-gray-300 rounded-lg px-2 py-1 text-gray-600 hover:bg-gray-50"
          >
            Grid
          </button>

          <button
            onClick={() => setShowConfirm(true)}
            className="ml-auto sm:ml-0 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg transition-colors"
          >
            Submit
          </button>
        </div>
      </header>

      {/* ── Main layout ── */}
      <div className="flex-1 flex max-w-5xl mx-auto w-full px-4 py-5 gap-5">

        {/* Question area */}
        <main className="flex-1 min-w-0 flex flex-col gap-4">
          <QuestionCard
            question={currentQuestion}
            selectedAnswer={selectedAnswer}
            onAnswer={handleAnswer}
          />

          {/* Prev / Flag / Next */}
          <div className="flex items-center justify-between">
            <button
              onClick={() => handleNavigate(currentIndex - 1)}
              disabled={currentIndex === 0}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700
                hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              ← Prev
            </button>

            <button
              onClick={handleToggleFlag}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-lg border text-sm font-medium transition-colors ${
                isFlagged
                  ? 'bg-orange-50 border-orange-400 text-orange-700'
                  : 'border-gray-300 text-gray-500 hover:bg-gray-50'
              }`}
            >
              {isFlagged ? '⚑ Flagged' : '⚐ Flag'}
            </button>

            {isLast ? (
              <button
                onClick={() => setShowConfirm(true)}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition-colors"
              >
                Finish ✓
              </button>
            ) : (
              <button
                onClick={() => handleNavigate(currentIndex + 1)}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors"
              >
                Next →
              </button>
            )}
          </div>

          {/* Question meta */}
          <p className="text-center text-xs text-gray-400">
            NEET {currentQuestion.year} · Q{currentQuestion.q_number} · {currentQuestion.topic}
          </p>
        </main>

        {/* Sidebar grid — desktop */}
        <aside className="hidden sm:block w-52 flex-shrink-0">
          <QuestionGrid
            questions={questions}
            answers={answers}
            flagged={flagged}
            currentIndex={currentIndex}
            onNavigate={handleNavigate}
          />
        </aside>
      </div>

      {/* ── Mobile grid overlay ── */}
      {showGrid && (
        <div
          className="absolute inset-0 z-30 bg-black/40 sm:hidden"
          onClick={() => setShowGrid(false)}
        >
          <div
            className="absolute right-0 top-0 bottom-0 w-72 bg-white shadow-xl p-4 overflow-y-auto"
            onClick={e => e.stopPropagation()}
          >
            <div className="flex justify-between items-center mb-3">
              <span className="font-semibold text-gray-800 text-sm">Questions</span>
              <button onClick={() => setShowGrid(false)} className="text-gray-400 hover:text-gray-600 text-sm">✕</button>
            </div>
            <QuestionGrid
              questions={questions}
              answers={answers}
              flagged={flagged}
              currentIndex={currentIndex}
              onNavigate={i => { handleNavigate(i); setShowGrid(false) }}
            />
          </div>
        </div>
      )}

      {/* ── Submit confirmation modal ── */}
      {showConfirm && (
        <div className="absolute inset-0 z-40 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl p-6 w-full max-w-sm space-y-4">
            <h2 className="text-lg font-bold text-gray-900">Submit quiz?</h2>

            <div className="space-y-1 text-sm text-gray-600">
              <p>
                Answered:{' '}
                <span className="font-semibold text-gray-900">{answeredCount}</span>
                {' '}/ {questions.length}
              </p>
              {unansweredCount > 0 && (
                <p className="text-orange-600">
                  {unansweredCount} question{unansweredCount !== 1 ? 's' : ''} unanswered
                </p>
              )}
              {flaggedCount > 0 && (
                <p className="text-orange-500">
                  {flaggedCount} question{flaggedCount !== 1 ? 's' : ''} flagged for review
                </p>
              )}
            </div>

            <div className="flex gap-3 pt-1">
              <button
                onClick={() => setShowConfirm(false)}
                className="flex-1 py-2 border border-gray-300 rounded-xl text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Go back
              </button>
              <button
                onClick={handleConfirmSubmit}
                className="flex-1 py-2 bg-green-600 hover:bg-green-700 text-white rounded-xl text-sm font-semibold transition-colors"
              >
                Submit
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  )
}
