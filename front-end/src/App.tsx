import { useEffect, useState } from 'react'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

function App() {
  const [message, setMessage] = useState('…')

  useEffect(() => {
    fetch(`${API_URL}/`)
      .then((res) => res.json() as Promise<{ message: string }>)
      .then((data) => setMessage(data.message))
      .catch(() => setMessage('Could not reach the API'))
  }, [])

  return (
    <main className="flex min-h-svh flex-col items-center justify-center gap-4 bg-white text-slate-900 dark:bg-slate-900 dark:text-slate-100">
      <h1 className="text-4xl font-semibold tracking-tight">{message}</h1>
      <p className="text-slate-500 dark:text-slate-400">Vite + React + TypeScript + Tailwind</p>
    </main>
  )
}

export default App
