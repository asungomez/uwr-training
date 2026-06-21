import { useEffect, useState } from 'react'

// Same-origin: requests to /api are proxied to the back-end (Vite in dev,
// a Render rewrite in prod), so no absolute API URL is needed.
const API_BASE = import.meta.env.VITE_API_URL ?? '/api'

function App() {
  const [message, setMessage] = useState('…')

  useEffect(() => {
    fetch(`${API_BASE}/`)
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
