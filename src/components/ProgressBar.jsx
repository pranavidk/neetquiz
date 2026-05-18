export default function ProgressBar({ value, max, className = '' }) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
        <div
          className="h-full bg-blue-500 rounded-full transition-all duration-300"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs text-gray-400 tabular-nums flex-shrink-0">
        {value}/{max}
      </span>
    </div>
  )
}
