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

function RegisterLacticAcidTestPage() {
  const navigate = useNavigate()
  const toast = useToast()
  const [rootError, setRootError] = useState<string | undefined>(undefined)
  const [submitting, setSubmitting] = useState(false)
  const [personalBest, setPersonalBest] = useState('')
  const [testResult, setTestResult] = useState('')
  const [weekId, setWeekId] = useState('')

  const form = useQuery('/lactic-acid-test-logs/form', {})
  // Latest personal best (seconds) — computes pool items' target times in the warmup PDF.
  // (Distinct from the `personalBest` form field for the test being recorded below.)
  const { data: latestPb } = useQuery('/lactic-acid-test-logs/latest-personal-best', {})
  const latestPbSeconds = latestPb?.seconds ?? null

  // Pre-select the recommended week once the form loads (resynced if it changes).
  const [syncedForm, setSyncedForm] = useState(form.data)
  if (form.data !== syncedForm) {
    setSyncedForm(form.data)
    setWeekId(form.data?.recommended_week_id ?? '')
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    setRootError(undefined)

    // Both fields are optional, but at least one must be present. Parse only the
    // ones that were filled in, allowing a comma as the decimal separator.
    const parse = (raw: string): number | null | 'invalid' => {
      if (raw.trim() === '') return null
      const value = Number(raw.replace(',', '.'))
      return Number.isFinite(value) && value > 0 ? value : 'invalid'
    }
    const pb = parse(personalBest)
    const result = parse(testResult)
    if (pb === 'invalid' || result === 'invalid') {
      setRootError('Introduce un tiempo válido en segundos.')
      return
    }
    if (pb === null && result === null) {
      setRootError('Introduce al menos una de las dos marcas.')
      return
    }

    setSubmitting(true)
    const { error: postError } = await api.POST('/lactic-acid-test-logs', {
      body: { personal_best: pb, test_result: result, week_id: weekId || null },
    })
    setSubmitting(false)
    if (postError) {
      setRootError(errorMessage(postError))
      return
    }
    toast.success('Prueba registrada.')
    void navigate('/pruebas/acido-lactico')
  }

  return (
    <section>
      <nav
        className="flex flex-wrap items-center gap-1 text-sm break-words text-slate-400"
        aria-label="Migas de pan"
      >
        <Link to="/pruebas/acido-lactico" className="transition-colors hover:text-slate-200">
          Prueba de ácido láctico
        </Link>
        <ChevronRight size={14} />
        <span className="text-slate-200">Registrar</span>
      </nav>

      <h1 className="mt-6 text-2xl font-semibold tracking-tight text-slate-100">
        Registrar prueba de ácido láctico
      </h1>

      {form.isLoading && <p className="mt-4 text-slate-400">Cargando…</p>}
      {form.error && <p className="mt-4 text-red-400">No se ha podido cargar la prueba.</p>}

      {form.data && (
        // Desktop: two columns — warmup on the left, the form on the right. Single
        // column on mobile, warmup first.
        <div className="mt-6 flex flex-col gap-10 lg:grid lg:grid-cols-2 lg:items-start lg:gap-10">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-lg font-semibold text-slate-100">Calentamiento</h2>
              <button
                type="button"
                onClick={() => form.data && openTrainingPdf(form.data.warmup, latestPbSeconds)}
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
            className="flex min-w-0 flex-col gap-8"
          >
            <div className="flex flex-col gap-2">
              <h2 className="text-lg font-semibold text-slate-100">Marca personal</h2>
              <p className="text-sm text-slate-400">
                50m (dos largos) del ejercicio llamado <i>cuartos</i>: sumérgete al fondo de la
                piscina e impúlsate de la pared. Natación subacuática hasta el centro de la piscina,
                con brazos en punta de flecha y piernas de delfín. A mitad de la piscina, asciende a
                la superficie y termina el largo en crol. Repite otros 25 metros para volver. Haz
                los 50 metros a máximo esfuerzo y anota el tiempo.
              </p>
              <label className="flex w-40 flex-col gap-1 text-sm font-medium text-slate-300">
                Tiempo (segundos)
                <input
                  type="number"
                  inputMode="decimal"
                  step="0.1"
                  min="0"
                  value={personalBest}
                  onChange={(event) => setPersonalBest(event.target.value)}
                  placeholder="40.5"
                  aria-label="Marca personal en segundos"
                  className={`${controlClass} mt-1 w-full text-sm`}
                />
              </label>
            </div>

            <div className="flex flex-col gap-2">
              <h2 className="text-lg font-semibold text-slate-100">Resultado de la prueba</h2>
              <p className="text-sm text-slate-400">
                Realiza el ejercicio anterior 8 veces en ciclos de 60 segundos. Se hacen 50 metros y
                se descansa lo que queda del minuto antes de volver a salir. Mide el tiempo que
                tardas en cada una de las 8 repeticiones, y haz la media.
              </p>
              <label className="flex w-40 flex-col gap-1 text-sm font-medium text-slate-300">
                Tiempo medio (segundos)
                <input
                  type="number"
                  inputMode="decimal"
                  step="0.1"
                  min="0"
                  value={testResult}
                  onChange={(event) => setTestResult(event.target.value)}
                  placeholder="44.5"
                  aria-label="Resultado en segundos"
                  className={`${controlClass} mt-1 w-full text-sm`}
                />
              </label>
            </div>

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

            <div className="flex flex-col gap-4">
              <FormError message={rootError} />
              <SubmitButton pending={submitting} pendingLabel="Guardando…">
                Finalizar prueba
              </SubmitButton>
            </div>
          </form>
        </div>
      )}
    </section>
  )
}

export default RegisterLacticAcidTestPage
