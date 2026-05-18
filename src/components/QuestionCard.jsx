import { useState, useEffect } from 'react'
import OptionButton from './OptionButton.jsx'

const LABELS = ['A', 'B', 'C', 'D']

// onAnswer is called with 1|2|3|4 (1-indexed, matching correct_answer in the data)
export default function QuestionCard({ question, selectedAnswer, onAnswer }) {
  const isCanceled = question.correct_answer === null
  const [lightbox, setLightbox] = useState(false)

  useEffect(() => {
    if (!lightbox) return
    const onKey = (e) => { if (e.key === 'Escape') setLightbox(false) }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [lightbox])

  return (
    <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-5 flex flex-col gap-4">

      {isCanceled && (
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-yellow-50 border border-yellow-300 text-yellow-800 text-sm">
          <span className="text-base leading-none">⊘</span>
          <span>
            <strong>NTA Canceled</strong> — no official answer; won't affect your score.
          </span>
        </div>
      )}

      {question.has_image && question.image_path ? (
        <>
          <div className="flex justify-center">
            <img
              src={`${import.meta.env.BASE_URL}${question.image_path}`}
              alt="Question diagram"
              className="max-w-full max-h-80 object-contain rounded-lg border border-gray-100 cursor-zoom-in"
              loading="lazy"
              onClick={() => setLightbox(true)}
            />
          </div>

          {lightbox && (
            <div
              className="fixed inset-0 z-50 flex items-center justify-center bg-black/80"
              onClick={() => setLightbox(false)}
            >
              <img
                src={`${import.meta.env.BASE_URL}${question.image_path}`}
                alt="Question diagram"
                className="max-w-[90vw] max-h-[90vh] object-contain rounded-lg shadow-2xl"
                onClick={(e) => e.stopPropagation()}
              />
            </div>
          )}
        </>
      ) : (
        <>
          <p className="text-gray-900 text-base leading-relaxed whitespace-pre-wrap">
            {question.text}
          </p>
          {(question.subject === 'Physics' || question.subject === 'Chemistry') && (
            <p className="text-xs text-amber-600">
              Note: mathematical symbols may not display correctly
            </p>
          )}
        </>
      )}

      <div className="flex flex-col gap-2">
        {question.options.map((text, i) => (
          <OptionButton
            key={i}
            label={LABELS[i]}
            text={text}
            selected={selectedAnswer === i + 1}
            onClick={() => onAnswer(i + 1)}
            variant={isCanceled ? 'neutral' : 'quiz'}
          />
        ))}
      </div>

    </div>
  )
}
