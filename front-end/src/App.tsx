import { Navigate, Route, Routes } from 'react-router-dom'

import AdminRoute from './auth/AdminRoute'
import { useAuth } from './auth/context'
import AppLayout from './layout/AppLayout'
import AcceptInvitationPage from './pages/AcceptInvitationPage'
import LoginPage from './pages/LoginPage'
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

  return (
    <Routes>
      {/* Public: reachable whether or not you're logged in. */}
      <Route path="/aceptar-invitacion/:token" element={<AcceptInvitationPage />} />

      {!user ? (
        <Route path="*" element={<LoginPage />} />
      ) : (
        <Route element={<AppLayout />}>
          <Route index element={<Navigate to="/entrenamientos" replace />} />
          <Route path="/entrenamientos" element={<TrainingsPage />} />
          <Route path="/usuarios" element={<AdminRoute />}>
            <Route index element={<UsersPage />} />
            <Route path=":id" element={<UserDetailPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/entrenamientos" replace />} />
        </Route>
      )}
    </Routes>
  )
}

export default App
