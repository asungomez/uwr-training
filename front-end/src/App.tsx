import { Navigate, Route, Routes } from 'react-router-dom'

import LoginForm from './LoginForm'
import AdminRoute from './auth/AdminRoute'
import { useAuth } from './auth/context'
import AppLayout from './layout/AppLayout'
import TrainingsPage from './pages/TrainingsPage'
import UserDetailPage from './pages/UserDetailPage'
import UsersPage from './pages/UsersPage'

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

  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<Navigate to="/entrenamientos" replace />} />
        <Route path="/entrenamientos" element={<TrainingsPage />} />
        <Route path="/usuarios" element={<AdminRoute />}>
          <Route index element={<UsersPage />} />
          <Route path=":id" element={<UserDetailPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/entrenamientos" replace />} />
      </Route>
    </Routes>
  )
}

export default App
