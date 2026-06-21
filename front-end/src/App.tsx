import { Navigate, Route, Routes } from 'react-router-dom'

import LoginForm from './LoginForm'
import { useAuth } from './auth/context'
import AppLayout from './layout/AppLayout'
import EntrenamientosPage from './pages/EntrenamientosPage'
import UsuariosPage from './pages/UsuariosPage'

function App() {
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return (
      <main className="flex min-h-svh items-center justify-center bg-slate-900 text-slate-400">
        Cargando…
      </main>
    )
  }

  if (!user) {
    return (
      <main className="flex min-h-svh flex-col items-center justify-center gap-8 bg-slate-900 px-4 text-slate-100">
        <h1 className="text-4xl font-semibold tracking-tight">UWR entrenamiento</h1>
        <LoginForm />
      </main>
    )
  }

  const isAdmin = user.role === 'admin'

  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<Navigate to="/entrenamientos" replace />} />
        <Route path="/entrenamientos" element={<EntrenamientosPage />} />
        <Route
          path="/usuarios"
          element={isAdmin ? <UsuariosPage /> : <Navigate to="/entrenamientos" replace />}
        />
        <Route path="*" element={<Navigate to="/entrenamientos" replace />} />
      </Route>
    </Routes>
  )
}

export default App
