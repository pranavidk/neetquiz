// Colour priority (highest → lowest):
//   canceled               → purple
//   flagged + answered     → deep orange
//   flagged only           → light orange
//   answered               → green
//   current (ring only)    → blue ring, keeps bg colour above
//   default                → gray

function cellStyle(q, i, answers, flagged, currentIndex) {
  const answered = answers[q.id] != null
  const isFlagged  = flagged.has(q.id)
  const isCanceled = q.correct_answer === null
  const isCurrent  = i === currentIndex

  let bg
  if (isCanceled)              bg = 'bg-purple-100 text-purple-700'
  else if (isFlagged && answered) bg = 'bg-orange-300 text-orange-900'
  else if (isFlagged)          bg = 'bg-orange-100 text-orange-700'
  else if (answered)           bg = 'bg-green-100 text-green-800'
  else                         bg = 'bg-gray-100 text-gray-500'

  const ring = isCurrent ? 'ring-2 ring-blue-500 ring-offset-1' : ''

  return `${bg} ${ring}`
}

const LEGEND = [
  { cls: 'bg-green-100',  label: 'Answered'     },
  { cls: 'bg-orange-100', label: 'Flagged'       },
  { cls: 'bg-purple-100', label: 'NTA Canceled'  },
  { cls: 'bg-gray-100',   label: 'Not answered'  },
]

export default function QuestionGrid({ questions, answers, flagged, currentIndex, onNavigate }) {
  const answeredCount = Object.values(answers).filter(v => v != null).length

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-3 space-y-3">
      <div className="flex justify-between items-center">
        <span className="text-xs font-semibold text-gray-700">Questions</span>
        <span className="text-xs text-gray-400">{answeredCount} / {questions.length}</span>
      </div>

      <div className="grid grid-cols-5 gap-1">
        {questions.map((q, i) => (
          <button
            key={q.id}
            onClick={() => onNavigate(i)}
            title={`Q${i + 1} · ${q.topic}`}
            className={`w-8 h-8 rounded text-xs font-medium transition-opacity hover:opacity-70
              ${cellStyle(q, i, answers, flagged, currentIndex)}`}
          >
            {i + 1}
          </button>
        ))}
      </div>

      <div className="space-y-1 pt-1 border-t border-gray-100">
        {LEGEND.map(({ cls, label }) => (
          <div key={label} className="flex items-center gap-2">
            <span className={`w-3 h-3 rounded-sm flex-shrink-0 ${cls} border border-gray-200`} />
            <span className="text-xs text-gray-400">{label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
