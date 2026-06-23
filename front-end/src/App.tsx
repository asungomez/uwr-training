import { Navigate, Route, Routes } from 'react-router-dom'

import AdminRoute from '@/auth/AdminRoute'
import { useAuth } from '@/auth/context'
import AppLayout from '@/components/features/layout/AppLayout'
import AcceptInvitationPage from '@/pages/accept-invitation/[token]/AcceptInvitationPage'
import ExercisesPage from '@/pages/exercises/ExercisesPage'
import ForgotPasswordPage from '@/pages/forgot-password/ForgotPasswordPage'
import LoginPage from '@/pages/login/LoginPage'
import TrainingsPage from '@/pages/trainings/TrainingsPage'
import UserDetailPage from '@/pages/users/[id]/UserDetailPage'
import UsersPage from '@/pages/users/UsersPage'

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
      <Route path="/recuperar-contrasena" element={<ForgotPasswordPage />} />

      {!user ? (
        <Route path="*" element={<LoginPage />} />
      ) : (
        <Route element={<AppLayout />}>
          <Route index element={<Navigate to="/entrenamientos" replace />} />
          <Route path="/entrenamientos" element={<TrainingsPage />} />
          <Route path="/ejercicios" element={<ExercisesPage />} />
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
