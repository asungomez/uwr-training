import LoginForm from './LoginForm'
import { useAuth } from './auth/context'

function App() {
  const { user, isLoading, logout } = useAuth()

  return (
    <main className="flex min-h-svh flex-col items-center justify-center gap-8 bg-slate-900 px-4 text-slate-100">
      <h1 className="text-4xl font-semibold tracking-tight">UWR entrenamiento</h1>

      {isLoading ? (
        <p className="text-slate-400">Cargando…</p>
      ) : user ? (
        <div className="flex flex-col items-center gap-4">
          <p className="text-slate-300">
            Sesión iniciada como <span className="font-medium text-slate-100">{user.email}</span>
          </p>
          <button
            type="button"
            onClick={() => {
              void logout()
            }}
            className="rounded-md border border-slate-600 px-4 py-2 font-medium text-slate-200 transition-colors hover:bg-slate-800 focus:ring-2 focus:ring-indigo-400 focus:outline-none"
          >
            Cerrar sesión
          </button>
        </div>
      ) : (
        <LoginForm />
      )}
    </main>
  )
}

export default App
