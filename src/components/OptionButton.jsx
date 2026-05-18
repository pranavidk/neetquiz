// variant: 'quiz' | 'correct' | 'wrong' | 'missed' | 'neutral'
//
// quiz    — default during an active session; selected state drives the colour
// correct — answer was right (review mode)
// wrong   — user's answer was wrong (review mode)
// missed  — correct answer the user didn't pick (review mode)
// neutral — NTA-canceled options, or unselected options in review mode

const STYLES = {
  quiz: {
    selected:   'bg-blue-600 border-blue-600 text-white',
    unselected: 'bg-white border-gray-300 text-gray-800 hover:border-blue-400 hover:bg-blue-50',
    label: {
      selected:   'bg-white/20 text-white',
      unselected: 'bg-gray-100 text-gray-500',
    },
  },
  correct: {
    base:  'bg-green-50 border-green-500 text-green-900',
    label: 'bg-green-200 text-green-800',
  },
  wrong: {
    base:  'bg-red-50 border-red-500 text-red-900',
    label: 'bg-red-200 text-red-800',
  },
  missed: {
    base:  'bg-green-50 border-green-400 border-dashed text-green-800',
    label: 'bg-green-100 text-green-700',
  },
  neutral: {
    base:  'bg-white border-gray-200 text-gray-500',
    label: 'bg-gray-100 text-gray-400',
  },
}

export default function OptionButton({ label, text, selected, onClick, variant = 'quiz', disabled = false }) {
  const s = STYLES[variant]

  let containerCls, labelCls
  if (variant === 'quiz') {
    containerCls = selected ? s.selected : s.unselected
    labelCls = selected ? s.label.selected : s.label.unselected
  } else {
    containerCls = s.base
    labelCls = s.label
  }

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`w-full flex items-start gap-3 px-4 py-3 rounded-xl border text-left transition-colors
        ${containerCls} ${disabled ? 'cursor-default' : 'cursor-pointer'}`}
    >
      <span className={`mt-0.5 flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${labelCls}`}>
        {label}
      </span>
      <span className="flex-1 text-sm leading-relaxed">{text}</span>
    </button>
  )
}
