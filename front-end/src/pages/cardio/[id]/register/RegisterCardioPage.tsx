import { ChevronRight, Timer } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { api, useQuery } from '@/api/client'
import { errorMessage } from '@/api/errors'
import { controlClass } from '@/components/atoms/form/fieldStyles'
import FormError from '@/components/atoms/form/FormError'
import SelectControl from '@/components/atoms/form/SelectControl'
import SubmitButton from '@/components/atoms/form/SubmitButton'
import CardioItemView from '@/components/features/cardio/CardioItemView'
import CardioTimer from '@/components/features/cardio/CardioTimer'
import { useToast } from '@/components/toast/context'

function RegisterCardioPage() {
  const { id } = useParams<{ id: string }>()
  const trainingId = id ?? ''
  const navigate = useNavigate()
  const toast = useToast()
  const [rootError, setRootError] = useState<string | undefined>(undefined)
  const [submitting, setSubmitting] = useState(false)
  const [exercise, setExercise] = useState('')
  const [note, setNote] = useState('')
  const [weekId, setWeekId] = useState('')
  const [timerOpen, setTimerOpen] = useState(false)

  // The assignable weeks (those recommending this cardio type, not yet full) and
  // the recommended one to pre-select.
  const form = useQuery('/cardio-trainings/{training_id}/log-form', {
    params: { path: { training_id: trainingId } },
  })
  // The session itself (its blocks/intervals), shown read-only so the athlete can
  // follow it while logging — consistent with the gym/pool register flow.
  const training = useQuery('/cardio-trainings/{training_id}', {
    params: { path: { training_id: trainingId } },
  })

  // Pre-select the recommended week once the form loads (resynced if it changes);
  // tracked separately so a manual choice isn't clobbered on re-render.
  const [syncedForm, setSyncedForm] = useState(form.data)
  if (form.data !== syncedForm) {
    setSyncedForm(form.data)
    setWeekId(form.data?.recommended_week_id ?? '')
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    setSubmitting(true)
    setRootError(undefined)

    const { error: postError } = await api.POST('/cardio-trainings/{training_id}/logs', {
      params: { path: { training_id: trainingId } },
      body: {
        exercise: exercise.trim() || null,
        note: note.trim() || null,
        week_id: weekId || null,
      },
    })
    setSubmitting(false)
    if (postError) {
      setRootError(errorMessage(postError))
      return
    }
    toast.success('Sesión registrada.')
    void navigate(`/entrenamientos/cardio/sesion/${trainingId}`)
  }

  return (
    <section>
      <nav
        className="flex flex-wrap items-center gap-1 text-sm break-words text-slate-400"
        aria-label="Migas de pan"
      >
        <Link to="/entrenamientos" className="transition-colors hover:text-slate-200">
          Entrenamientos
        </Link>
        <ChevronRight size={14} />
        <Link to="/entrenamientos/cardio" className="transition-colors hover:text-slate-200">
          Cardio
        </Link>
        <ChevronRight size={14} />
        <Link
          to={`/entrenamientos/cardio/sesion/${trainingId}`}
          className="transition-colors hover:text-slate-200"
        >
          {form.data?.title ?? '…'}
        </Link>
        <ChevronRight size={14} />
        <span className="text-slate-200">Registrar</span>
      </nav>

      {form.isLoading && <p className="mt-4 text-slate-400">Cargando…</p>}
      {form.error && <p className="mt-4 text-red-400">No se ha encontrado el entrenamiento.</p>}

      {form.data && (
        <div className="mt-6 max-w-2xl">
          <h1 className="text-2xl font-semibold tracking-tight text-slate-100">Registrar sesión</h1>
          <p className="mt-1 text-slate-400">{form.data.title ?? 'Sin título'}</p>

          {/* Live timer to follow the session on the machine. Only when there are
              timed blocks. */}
          {training.data?.items.some((item) => item.kind === 'block') && (
            <button
              type="button"
              onClick={() => setTimerOpen(true)}
              className="mt-4 inline-flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-500 focus:ring-2 focus:ring-indigo-400 focus:outline-none"
            >
              <Timer size={16} />
              Iniciar crono
            </button>
          )}

          {/* The session itself, read-only, so the athlete can follow it while logging. */}
          {training.data && training.data.items.length > 0 && (
            <div className="mt-6 flex flex-col gap-3">
              {training.data.items.map((item) => (
                <CardioItemView key={item.id} item={item} />
              ))}
            </div>
          )}

          <form
            onSubmit={(event) => void handleSubmit(event)}
            noValidate
            className="mt-6 flex flex-col gap-4 border-t border-slate-800 pt-6"
          >
            <label className="flex flex-col gap-1 text-sm font-medium text-slate-300">
              Actividad (opcional)
              <input
                type="text"
                value={exercise}
                onChange={(event) => setExercise(event.target.value)}
                placeholder="Carrera, remo, bici…"
                className={`${controlClass} mt-1 w-full text-sm`}
              />
            </label>

            <label className="flex flex-col gap-1 text-sm font-medium text-slate-300">
              Nota de la sesión (opcional)
              <textarea
                value={note}
                onChange={(event) => setNote(event.target.value)}
                rows={3}
                placeholder="Algo que recordar para la próxima vez…"
                className={`${controlClass} mt-1 w-full text-sm`}
              />
            </label>

            {form.data.weeks.length > 0 && (
              <label className="flex max-w-sm flex-col gap-1 text-sm font-medium text-slate-300">
                Semana (opcional)
                <SelectControl
                  value={weekId}
                  onChange={(event) => setWeekId(event.target.value)}
                  aria-label="Semana"
                  className={`${controlClass} mt-1 w-full text-sm`}
                  options={[
                    { value: '', label: 'Sin semana' },
                    ...form.data.weeks.map((week) => ({ value: week.id, label: week.name })),
                  ]}
                />
              </label>
            )}

            <FormError message={rootError} />
            <SubmitButton pending={submitting} pendingLabel="Guardando…">
              Finalizar sesión
            </SubmitButton>
          </form>
        </div>
      )}

      {timerOpen && training.data && (
        <CardioTimer training={training.data} onClose={() => setTimerOpen(false)} />
      )}
    </section>
  )
}

export default RegisterCardioPage
