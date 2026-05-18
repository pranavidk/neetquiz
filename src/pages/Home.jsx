import { useNavigate } from 'react-router-dom'
import { metadata } from '../data/questions.js'
import { useLocalStorage } from '../hooks/useLocalStorage.js'

const { totalCount, years, topics } = metadata
const yearRange = `${years[0]}–${years[years.length - 1]}`

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })
}

export default function Home() {
  const navigate = useNavigate()
  const [attempts] = useLocalStorage('neet_attempts', [])
  const recent = attempts.slice(-3).reverse()

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 py-12">
      <div className="w-full max-w-md space-y-8">

        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">NEET PYQ Quiz</h1>
          <p className="mt-1 text-gray-500">
            Previous-year questions across Physics, Chemistry and Biology.
          </p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-3">
          <StatCard value={totalCount} label="Questions" />
          <StatCard value={yearRange} label="Years" />
          <StatCard value={topics.length} label="Topics" />
        </div>

        {/* Actions */}
        <div className="flex flex-col gap-3">
          <button
            onClick={() => navigate('/config', { state: { mode: 'mock' } })}
            className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl transition-colors"
          >
            Start mock test
          </button>
          <button
            onClick={() => navigate('/config')}
            className="w-full py-3 bg-white hover:bg-gray-50 text-gray-700 font-semibold rounded-xl border border-gray-300 transition-colors"
          >
            Custom quiz
          </button>
        </div>

        {/* Attempt history */}
        <div>
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
            Recent attempts
          </p>
          {recent.length === 0 ? (
            <p className="text-sm text-gray-400">No attempts yet. Start a quiz above.</p>
          ) : (
            <ul className="space-y-1">
              {recent.map((a, i) => (
                <li key={i} className="flex justify-between text-sm text-gray-600">
                  <span>{formatDate(a.date)}</span>
                  <span className="tabular-nums">
                    {a.score} / {a.total * 4}
                    <span className="text-gray-400 ml-1">({a.total}q)</span>
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>

      </div>
    </div>
  )
}

function StatCard({ value, label }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-3 text-center">
      <div className="text-xl font-bold text-gray-900">{value}</div>
      <div className="text-xs text-gray-400 mt-0.5">{label}</div>
    </div>
  )
}
