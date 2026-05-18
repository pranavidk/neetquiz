import { useState, useEffect, useRef } from 'react'

// timeLimit — seconds
// startTime — Date.now() timestamp
// onExpire  — called once when countdown hits zero
export default function Timer({ timeLimit, startTime, onExpire }) {
  const [remaining, setRemaining] = useState(() =>
    Math.max(0, timeLimit - Math.floor((Date.now() - startTime) / 1000))
  )
  const firedRef = useRef(false)

  useEffect(() => {
    const id = setInterval(() => {
      const rem = Math.max(0, timeLimit - Math.floor((Date.now() - startTime) / 1000))
      setRemaining(rem)
      if (rem === 0 && !firedRef.current) {
        firedRef.current = true
        onExpire()
      }
    }, 500)
    return () => clearInterval(id)
  }, [timeLimit, startTime, onExpire])

  const mins = Math.floor(remaining / 60)
  const secs = remaining % 60
  const isRed    = remaining < 300           // < 5 min
  const isYellow = remaining < 600 && !isRed // 5–10 min

  return (
    <span
      className={`font-mono font-bold tabular-nums text-sm ${
        isRed ? 'text-red-600 animate-pulse' : isYellow ? 'text-yellow-600' : 'text-gray-700'
      }`}
    >
      {String(mins).padStart(2, '0')}:{String(secs).padStart(2, '0')}
    </span>
  )
}
