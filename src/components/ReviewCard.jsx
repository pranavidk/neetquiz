import { useState } from 'react'
import OptionButton from './OptionButton.jsx'
import MathText from './MathText.jsx'

const LABELS = ['A', 'B', 'C', 'D']

function reformatMatchColumn(text) {
  if (!text) return text
  let out = text.replace(/([^\n])\s+(Column[\s-][IVX]+)/gi, '$1\n$2')
  const hits = (out.match(/\(?\b[PQRS][.)]\s/g) || []).length
  if (hits < 3) return out
  out = out.replace(/([^\n])\s+\(?([PQRS])[.)]\s/g, (_, pre, lbl) => `${pre}\n${lbl}. `)
  const abcHits = (out.match(/\(?\b[ABCD][.)]\s/g) || []).length
  if (abcHits >= 3) {
    out = out.replace(/([^\n])\s+\(?([ABCD])[.)]\s/g, (_, pre, lbl) => `${pre}\n${lbl}. `)
  }
  return out
}

function getStatus(question, userAnswer) {
  if (question.correct_answer === null)    return 'canceled'
  if (userAnswer == null)                  return 'unanswered'
  if (userAnswer === question.correct_answer) return 'correct'
  return 'wrong'
}

// i is 0-indexed; options are compared as i+1 against 1-indexed correct_answer/userAnswer
function optionVariant(i, question, userAnswer, status) {
  const optNum = i + 1
  if (status === 'canceled')                      return 'neutral'
  if (optNum === question.correct_answer)          return 'correct'
  if (optNum === userAnswer && status === 'wrong') return 'wrong'
  return 'neutral'
}

const STATUS_BADGE = {
  correct:    { icon: '✓', label: 'Correct',      cls: 'bg-green-100 text-green-700'  },
  wrong:      { icon: '✗', label: 'Wrong',         cls: 'bg-red-100 text-red-700'     },
  unanswered: { icon: '–', label: 'Not answered',  cls: 'bg-gray-100 text-gray-500'   },
  canceled:   { icon: '⊘', label: 'NTA Canceled',  cls: 'bg-yellow-100 text-yellow-700' },
}

const BORDER = {
  correct:    'border-green-200',
  wrong:      'border-red-200',
  unanswered: 'border-gray-200',
  canceled:   'border-yellow-200',
}

export default function ReviewCard({ question, index, userAnswer }) {
  const [open, setOpen] = useState(false)
  const status = getStatus(question, userAnswer)
  const { icon, label, cls } = STATUS_BADGE[status]

  return (
    <div className={`bg-white rounded-xl border shadow-sm overflow-hidden ${BORDER[status]}`}>

      {/* Collapsed header — always visible */}
      <button
        onClick={() => setOpen(v => !v)}
        className="w-full flex items-start gap-3 px-4 py-3 text-left hover:bg-gray-50 transition-colors"
      >
        <span className="flex-shrink-0 mt-0.5 w-6 h-6 rounded-full bg-gray-100 text-gray-500 text-xs font-bold flex items-center justify-center">
          {index + 1}
        </span>

        <div className="flex-1 min-w-0">
          <div className="text-sm text-gray-700 line-clamp-2 leading-snug">
            <MathText text={question.text} />
          </div>
          <div className="mt-1.5 flex flex-wrap items-center gap-2">
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${cls}`}>
              {icon} {label}
            </span>
            {userAnswer != null && status !== 'canceled' && (
              <span className="text-xs text-gray-400">
                Your answer: <strong>{LABELS[userAnswer - 1]}</strong>
                {status === 'wrong' && (
                  <> · Correct: <strong className="text-green-600">{LABELS[question.correct_answer - 1]}</strong></>
                )}
              </span>
            )}
          </div>
        </div>

        <span className="flex-shrink-0 text-gray-300 text-xs mt-1">{open ? '▲' : '▼'}</span>
      </button>

      {/* Expanded body */}
      {open && (
        <div className="border-t border-gray-100 px-4 py-4 bg-gray-50 space-y-4">
          {question.has_image && question.image_path ? (
            <>
              <div className="flex justify-center">
                <img
                  src={`${import.meta.env.BASE_URL}${question.image_path}`}
                  alt="Question diagram"
                  className="max-w-full max-h-72 object-contain rounded-lg border border-gray-200"
                  loading="lazy"
                />
              </div>
              <p className="text-xs text-gray-400 whitespace-pre-wrap leading-relaxed">
                <MathText text={reformatMatchColumn(question.text)} />
              </p>
            </>
          ) : (
            <p className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">
              <MathText text={reformatMatchColumn(question.text)} />
            </p>
          )}

          <div className="flex flex-col gap-2">
            {question.options.map((text, i) => (
              <OptionButton
                key={i}
                label={LABELS[i]}
                text={<MathText text={text} />}
                selected={userAnswer === i + 1}
                variant={optionVariant(i, question, userAnswer, status)}
                disabled
              />
            ))}
          </div>

          {question.solution && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-3">
              <p className="text-xs font-semibold text-blue-600 uppercase tracking-wide mb-1">Solution</p>
              <div className="text-sm text-gray-600 whitespace-pre-wrap font-mono bg-gray-50 rounded p-3">
                <MathText text={question.solution} />
              </div>
            </div>
          )}

          <p className="text-xs text-gray-400">
            NEET {question.year} · Q{question.q_number} · {question.subject} · {question.topic}
          </p>
        </div>
      )}

    </div>
  )
}

