import { Navigate, Route, Routes } from 'react-router-dom'

import AdminRoute from '@/auth/AdminRoute'
import { useAuth } from '@/auth/context'
import AppLayout from '@/components/features/layout/AppLayout'
import AcceptInvitationPage from '@/pages/accept-invitation/[token]/AcceptInvitationPage'
import EditExercisePage from '@/pages/exercises/[id]/edit/EditExercisePage'
import ExerciseDetailPage from '@/pages/exercises/[id]/ExerciseDetailPage'
import ExercisesPage from '@/pages/exercises/ExercisesPage'
import NewExercisePage from '@/pages/exercises/new/NewExercisePage'
import ForgotPasswordPage from '@/pages/forgot-password/ForgotPasswordPage'
import LoginPage from '@/pages/login/LoginPage'
import CardioDetailPage from '@/pages/cardio/[id]/CardioDetailPage'
import EditCardioPage from '@/pages/cardio/[id]/edit/EditCardioPage'
import CardioCategoryPage from '@/pages/cardio/CardioCategoryPage'
import CardioSubtypePage from '@/pages/cardio/CardioSubtypePage'
import NewCardioPage from '@/pages/cardio/new/NewCardioPage'
import EditTrainingPage from '@/pages/trainings/[id]/edit/EditTrainingPage'
import RegisterSessionPage from '@/pages/trainings/[id]/register/RegisterSessionPage'
import TrainingDetailPage from '@/pages/trainings/[id]/TrainingDetailPage'
import NewTrainingPage from '@/pages/trainings/new/NewTrainingPage'
import TrainingsLandingPage from '@/pages/trainings/TrainingsLandingPage'
import TrainingsPage from '@/pages/trainings/TrainingsPage'
import TrainingSubtypePage from '@/pages/trainings/TrainingSubtypePage'
import UserDetailPage from '@/pages/users/[id]/UserDetailPage'
import UsersPage from '@/pages/users/UsersPage'
import EditWeekPage from '@/pages/weeks/[id]/edit/EditWeekPage'
import WeekDetailPage from '@/pages/weeks/[id]/WeekDetailPage'
import NewWeekPage from '@/pages/weeks/new/NewWeekPage'
import WeeksPage from '@/pages/weeks/WeeksPage'

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
          <Route path="/entrenamientos">
            <Route index element={<TrainingsLandingPage />} />
            <Route element={<AdminRoute />}>
              <Route path=":id/editar" element={<EditTrainingPage />} />
            </Route>
            {/* Static category slugs rank above the dynamic :id detail route; each
                has a subtype-scoped list one level deeper, and creation is scoped
                under that subtype (category + subtype come from the URL). */}
            {['gimnasio', 'piscina'].map((categorySlug) => (
              <Route key={categorySlug} path={categorySlug}>
                <Route index element={<TrainingsPage />} />
                <Route path=":subtype" element={<TrainingSubtypePage />} />
                <Route element={<AdminRoute />}>
                  <Route path=":subtype/nuevo" element={<NewTrainingPage />} />
                </Route>
              </Route>
            ))}
            {/* Cardio is a fully separate model with its own endpoints/pages. Its
                detail lives under …/cardio/sesion/:id so it doesn't collide with
                the :subtype list route. */}
            <Route path="cardio">
              <Route index element={<CardioCategoryPage />} />
              <Route path=":subtype" element={<CardioSubtypePage />} />
              <Route element={<AdminRoute />}>
                <Route path=":subtype/nuevo" element={<NewCardioPage />} />
                <Route path="sesion/:id/editar" element={<EditCardioPage />} />
              </Route>
              <Route path="sesion/:id" element={<CardioDetailPage />} />
            </Route>
            {/* Any authenticated user can log a session they performed. */}
            <Route path=":id/registrar" element={<RegisterSessionPage />} />
            <Route path=":id" element={<TrainingDetailPage />} />
          </Route>
          <Route path="/ejercicios">
            <Route index element={<ExercisesPage />} />
            <Route element={<AdminRoute />}>
              <Route path="nuevo" element={<NewExercisePage />} />
              <Route path=":id/editar" element={<EditExercisePage />} />
            </Route>
            <Route path=":id" element={<ExerciseDetailPage />} />
          </Route>
          <Route path="/calendario">
            <Route index element={<WeeksPage />} />
            <Route element={<AdminRoute />}>
              <Route path="nueva" element={<NewWeekPage />} />
              <Route path=":id/editar" element={<EditWeekPage />} />
            </Route>
            <Route path=":id" element={<WeekDetailPage />} />
          </Route>
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
