import { ChevronRight } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { api, useQuery } from '@/api/client'
import { errorMessage } from '@/api/errors'
import { controlClass } from '@/components/atoms/form/fieldStyles'
import FormError from '@/components/atoms/form/FormError'
import SelectControl from '@/components/atoms/form/SelectControl'
import SubmitButton from '@/components/atoms/form/SubmitButton'
import { useToast } from '@/components/toast/context'

function RegisterStrengthTestPage() {
  const navigate = useNavigate()
  const toast = useToast()
  const [rootError, setRootError] = useState<string | undefined>(undefined)
  const [submitting, setSubmitting] = useState(false)
  const [weekId, setWeekId] = useState('')
  // Actual weight lifted, keyed by exercise id.
  const [actuals, setActuals] = useState<Record<string, string>>({})
  // "Now" captured once on mount (reading the clock during render is impure).
  const [now] = useState(() => Date.now())

  // First check there's a body weight (the targets are derived from it). The history
  // list is most-recent-first, so item 0 is the latest.
  const bodyweight = useQuery('/bodyweight-logs', {
    params: { query: { page: 1, page_size: 1 } },
  })
  const latestBodyweight = bodyweight.data?.items[0]
  const hasBodyweight = latestBodyweight != null

  // The targets are only as good as the body weight they're based on; warn (but
  // don't block) when the latest register is more than 15 days old.
  const STALE_DAYS = 15
  const bodyweightIsStale =
    latestBodyweight != null &&
    (now - new Date(latestBodyweight.recorded_at).getTime()) / 86_400_000 > STALE_DAYS

  // Only load the test form once we know a body weight exists (the endpoint 400s
  // otherwise). null skips the request.
  const form = useQuery('/strength-test-logs/form', hasBodyweight ? {} : null)

  // Pre-select the recommended week once the form loads (resynced if it changes).
  const [syncedForm, setSyncedForm] = useState(form.data)
  if (form.data !== syncedForm) {
    setSyncedForm(form.data)
    setWeekId(form.data?.recommended_week_id ?? '')
  }

  function setActual(exerciseId: string, value: string) {
    setActuals((prev) => ({ ...prev, [exerciseId]: value }))
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    setRootError(undefined)

    const exercises = form.data?.exercises ?? []
    const entries = exercises.map((exercise) => ({
      exercise_id: exercise.exercise_id,
      actual_weight_kg: Number((actuals[exercise.exercise_id] ?? '').replace(',', '.')),
    }))
    if (
      entries.some(
        (entry) => !Number.isFinite(entry.actual_weight_kg) || entry.actual_weight_kg <= 0,
      )
    ) {
      setRootError('Introduce el peso levantado en cada ejercicio.')
      return
    }

    setSubmitting(true)
    const { error: postError } = await api.POST('/strength-test-logs', {
      body: { entries, week_id: weekId || null },
    })
    setSubmitting(false)
    if (postError) {
      setRootError(errorMessage(postError))
      return
    }
    toast.success('Prueba registrada.')
    void navigate('/pruebas/fuerza')
  }

  const isLoading = bodyweight.isLoading || (hasBodyweight && form.isLoading)

  return (
    <section className="max-w-2xl">
      <nav className="flex items-center gap-1 text-sm text-slate-400" aria-label="Migas de pan">
        <Link to="/pruebas/fuerza" className="transition-colors hover:text-slate-200">
          Prueba de fuerza
        </Link>
        <ChevronRight size={14} />
        <span className="text-slate-200">Registrar</span>
      </nav>

      <h1 className="mt-6 text-2xl font-semibold tracking-tight text-slate-100">
        Registrar prueba de fuerza
      </h1>

      {isLoading && <p className="mt-4 text-slate-400">Cargando…</p>}

      {bodyweight.data && !hasBodyweight && (
        <div className="mt-6 rounded-lg border border-amber-500/40 bg-amber-500/10 p-4 text-sm text-amber-200">
          <p>
            Necesitas al menos un registro de peso corporal para hacer una prueba de fuerza, ya que
            la carga objetivo se calcula a partir de él.
          </p>
          <Link
            to="/registro-peso"
            className="mt-3 inline-flex font-medium text-amber-100 underline transition-colors hover:text-white"
          >
            Registrar peso
          </Link>
        </div>
      )}

      {hasBodyweight && form.data && (
        <div className="mt-6">
          <p className="text-sm text-slate-400">
            Peso corporal de referencia:{' '}
            <span className="text-slate-200">{form.data.bodyweight_kg} kg</span>
          </p>

          {bodyweightIsStale && (
            <div className="mt-3 rounded-lg border border-amber-500/40 bg-amber-500/10 p-4 text-sm text-amber-200">
              <p>
                El peso se usa como medida para calcular los objetivos de la prueba. Es preferible
                introducir un peso reciente.
              </p>
              <Link
                to="/registro-peso"
                className="mt-3 inline-flex font-medium text-amber-100 underline transition-colors hover:text-white"
              >
                Registrar peso
              </Link>
            </div>
          )}

          {form.data.exercises.length === 0 ? (
            <p className="mt-6 text-sm text-slate-500">
              La prueba de fuerza todavía no tiene ejercicios. Pide a tu entrenador que los añada.
            </p>
          ) : (
            <form
              onSubmit={(event) => void handleSubmit(event)}
              noValidate
              className="mt-6 flex flex-col gap-4"
            >
              <ul className="flex flex-col gap-3">
                {form.data.exercises.map((exercise) => (
                  <li
                    key={exercise.exercise_id}
                    className="flex flex-wrap items-end justify-between gap-3 rounded-lg border border-slate-700 bg-slate-800/50 p-4"
                  >
                    <div className="min-w-0">
                      <span className="font-medium text-slate-100">{exercise.exercise_name}</span>
                      <p className="text-sm text-slate-400">
                        Objetivo: {exercise.target_weight_kg} kg
                      </p>
                    </div>
                    <label className="flex w-32 flex-col gap-1 text-xs font-medium text-slate-400">
                      Peso levantado (kg)
                      <input
                        type="number"
                        inputMode="decimal"
                        step="0.1"
                        min="0"
                        value={actuals[exercise.exercise_id] ?? ''}
                        onChange={(event) => setActual(exercise.exercise_id, event.target.value)}
                        aria-label={`Peso levantado en ${exercise.exercise_name}`}
                        className={`${controlClass} w-full py-1.5 text-sm`}
                      />
                    </label>
                  </li>
                ))}
              </ul>

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
                Finalizar prueba
              </SubmitButton>
            </form>
          )}
        </div>
      )}
    </section>
  )
}

export default RegisterStrengthTestPage
