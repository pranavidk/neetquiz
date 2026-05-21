import { createContext, useContext, useEffect, useState } from 'react'
import { loadQuestions, computeMetadata } from '../data/questions.js'

const QuestionsContext = createContext(null)

export function QuestionsProvider({ children }) {
  const [state, setState] = useState({
    questions: [],
    metadata:  null,
    loading:   true,
    error:     null,
  })

  useEffect(() => {
    loadQuestions()
      .then(raw => setState({
        questions: raw,
        metadata:  computeMetadata(raw),
        loading:   false,
        error:     null,
      }))
      .catch(err => setState(prev => ({ ...prev, loading: false, error: err.message })))
  }, [])

  return (
    <QuestionsContext.Provider value={state}>
      {children}
    </QuestionsContext.Provider>
  )
}

export function useQuestions() {
  return useContext(QuestionsContext)
}
