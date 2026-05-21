import { useState, useEffect } from 'react'
import OptionButton from './OptionButton.jsx'
import MathText from './MathText.jsx'

const LABELS = ['A', 'B', 'C', 'D']

// Detect and reformat match-the-column questions so P/Q/R/S items appear on separate lines.
// Handles both "P. text" and "(P) text" label styles; only fires when ≥3 labels found.
function reformatMatchColumn(text) {
  if (!text) return text
  let out = text.replace(/([^\n])\s+(Column[\s-][IVX]+)/gi, '$1\n$2')
  // Count P/Q/R/S labels in both bare (P.) and parenthesised ((P)) forms
  const hits = (out.match(/\(?\b[PQRS][.)]\s/g) || []).length
  if (hits < 3) return out
  // Break before each label; strip the surrounding ( if present
  out = out.replace(/([^\n])\s+\(?([PQRS])[.)]\s/g, (_, pre, lbl) => `${pre}\n${lbl}. `)
  // If A/B/C/D Column-I items are also present, break those too
  const abcHits = (out.match(/\(?\b[ABCD][.)]\s/g) || []).length
  if (abcHits >= 3) {
    out = out.replace(/([^\n])\s+\(?([ABCD])[.)]\s/g, (_, pre, lbl) => `${pre}\n${lbl}. `)
  }
  return out
}

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
            <MathText text={reformatMatchColumn(question.text)} />
          </p>
        </>
      )}

      <div className="flex flex-col gap-2">
        {question.options.map((text, i) => (
          <OptionButton
            key={i}
            label={LABELS[i]}
            text={<MathText text={text} />}
            selected={selectedAnswer === i + 1}
            onClick={() => onAnswer(i + 1)}
            variant={isCanceled ? 'neutral' : 'quiz'}
          />
        ))}
      </div>

    </div>
  )
}

