import { Routes, Route, Navigate } from 'react-router-dom'
import { QuizProvider } from './context/QuizContext.jsx'
import Home from './pages/Home.jsx'
import Config from './pages/Config.jsx'
import Quiz from './pages/Quiz.jsx'
import Results from './pages/Results.jsx'

export default function App() {
  return (
    <QuizProvider>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/config" element={<Config />} />
        <Route path="/quiz" element={<Quiz />} />
        <Route path="/results" element={<Results />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </QuizProvider>
  )
}
