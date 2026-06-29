import { ChevronRight, FileText } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { api, useQuery } from '@/api/client'
import { errorMessage } from '@/api/errors'
import { controlClass } from '@/components/atoms/form/fieldStyles'
import FormError from '@/components/atoms/form/FormError'
import SelectControl from '@/components/atoms/form/SelectControl'
import SubmitButton from '@/components/atoms/form/SubmitButton'
import WarmupView from '@/components/features/tests/WarmupView'
import { openTrainingPdf } from '@/components/features/trainings/trainingPdf'
import { useToast } from '@/components/toast/context'

function RegisterSpeedTestPage() {
  const navigate = useNavigate()
  const toast = useToast()
  const [rootError, setRootError] = useState<string | undefined>(undefined)
  const [submitting, setSubmitting] = useState(false)
  const [seconds, setSeconds] = useState('')
  const [weekId, setWeekId] = useState('')

  const form = useQuery('/speed-test-logs/form', {})

  // Pre-select the recommended week once the form loads (resynced if it changes).
  const [syncedForm, setSyncedForm] = useState(form.data)
  if (form.data !== syncedForm) {
    setSyncedForm(form.data)
    setWeekId(form.data?.recommended_week_id ?? '')
  }

  const warmup = form.data?.warmup

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    setRootError(undefined)
    const value = Number(seconds.replace(',', '.'))
    if (!Number.isFinite(value) || value <= 0) {
      setRootError('Introduce el tiempo en segundos.')
      return
    }

    setSubmitting(true)
    const { error: postError } = await api.POST('/speed-test-logs', {
      body: { seconds: value, week_id: weekId || null },
    })
    setSubmitting(false)
    if (postError) {
      setRootError(errorMessage(postError))
      return
    }
    toast.success('Prueba registrada.')
    void navigate('/pruebas/velocidad')
  }

  return (
    <section className="max-w-2xl">
      <nav
        className="flex flex-wrap items-center gap-1 text-sm break-words text-slate-400"
        aria-label="Migas de pan"
      >
        <Link to="/pruebas/velocidad" className="transition-colors hover:text-slate-200">
          Prueba de velocidad
        </Link>
        <ChevronRight size={14} />
        <span className="text-slate-200">Registrar</span>
      </nav>

      <h1 className="mt-6 text-2xl font-semibold tracking-tight text-slate-100">
        Registrar prueba de velocidad
      </h1>

      {form.isLoading && <p className="mt-4 text-slate-400">Cargando…</p>}
      {form.error && <p className="mt-4 text-red-400">No se ha podido cargar la prueba.</p>}

      {form.data && (
        <>
          <div className="mt-6">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-lg font-semibold text-slate-100">Calentamiento</h2>
              <button
                type="button"
                onClick={() => warmup && openTrainingPdf(warmup)}
                className="inline-flex items-center gap-2 rounded-md border border-slate-600 px-4 py-2 text-sm font-medium text-slate-200 transition-colors hover:bg-slate-800 focus:ring-2 focus:ring-indigo-400 focus:outline-none"
              >
                <FileText size={16} />
                PDF
              </button>
            </div>
            <div className="mt-3">
              <WarmupView warmup={form.data.warmup} />
            </div>
          </div>

          <form
            onSubmit={(event) => void handleSubmit(event)}
            noValidate
            className="mt-8 flex flex-col gap-4 border-t border-slate-800 pt-6"
          >
            <label className="flex w-40 flex-col gap-1 text-sm font-medium text-slate-300">
              Tiempo (segundos)
              <input
                type="number"
                inputMode="decimal"
                step="0.1"
                min="0"
                value={seconds}
                onChange={(event) => setSeconds(event.target.value)}
                placeholder="11.5"
                aria-label="Tiempo en segundos"
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
              Finalizar prueba
            </SubmitButton>
          </form>
        </>
      )}
    </section>
  )
}

export default RegisterSpeedTestPage
