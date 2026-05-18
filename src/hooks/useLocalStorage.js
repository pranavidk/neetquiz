import { useState, useCallback } from 'react'

function readStorage(key, initial) {
  try {
    const item = localStorage.getItem(key)
    return item === null ? initial : JSON.parse(item)
  } catch {
    return initial
  }
}

function writeStorage(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch {
    // localStorage unavailable (private browsing, quota exceeded, etc.)
  }
}

export function useLocalStorage(key, initial) {
  const [value, setInMemory] = useState(() => readStorage(key, initial))

  const setValue = useCallback(updater => {
    setInMemory(prev => {
      const next = typeof updater === 'function' ? updater(prev) : updater
      writeStorage(key, next)
      return next
    })
  }, [key])

  return [value, setValue]
}
