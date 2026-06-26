import { ChevronRight } from 'lucide-react'
import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { api, useMutate, useQuery } from '@/api/client'
import { errorMessage } from '@/api/errors'
import { controlClass } from '@/components/atoms/form/fieldStyles'
import SelectControl from '@/components/atoms/form/SelectControl'
import { formatLogDate } from '@/components/features/trainings/logFormat'
import { useToast } from '@/components/toast/context'

function StrengthTestLogDetailPage() {
  const { logId } = useParams<{ logId: string }>()
  const id = logId ?? ''
  const toast = useToast()
  const mutate = useMutate()
  const [savingWeek, setSavingWeek] = useState(false)

  const { data, isLoading, error } = useQuery('/strength-test-logs/{log_id}', {
    params: { path: { log_id: id } },
  })
  // The weeks this log can be assigned to (those recommending a strength test).
  const form = useQuery('/strength-test-logs/form', {})

  async function changeWeek(weekId: string) {
    setSavingWeek(true)
    const { error: patchError } = await api.PATCH('/strength-test-logs/{log_id}/week', {
      params: { path: { log_id: id } },
      body: { week_id: weekId || null },
    })
    setSavingWeek(false)
    if (patchError) {
      toast.error(errorMessage(patchError))
      return
    }
    await mutate(['/strength-test-logs/{log_id}', { params: { path: { log_id: id } } }])
    toast.success('Semana actualizada.')
  }

  return (
    <section className="max-w-2xl">
      <nav className="flex items-center gap-1 text-sm text-slate-400" aria-label="Migas de pan">
        <Link to="/pruebas/fuerza" className="transition-colors hover:text-slate-200">
          Prueba de fuerza
        </Link>
        <ChevronRight size={14} />
        <span className="text-slate-200">Registro</span>
      </nav>

      {isLoading && <p className="mt-4 text-slate-400">Cargando…</p>}
      {error && <p className="mt-4 text-red-400">No se ha encontrado el registro.</p>}

      {data && (
        <div className="mt-6">
          <h1 className="text-2xl font-semibold tracking-tight text-slate-100">
            {formatLogDate(data.performed_at)}
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            Peso corporal de referencia:{' '}
            <span className="text-slate-200">{data.bodyweight_kg} kg</span>
          </p>

          {(() => {
            // Selectable weeks = those still open, plus the log's current week (which
            // may now be full but must stay selectable here).
            const options = (form.data?.weeks ?? []).map((week) => ({
              value: week.id,
              label: week.name,
            }))
            if (data.week_id && !options.some((o) => o.value === data.week_id)) {
              options.unshift({ value: data.week_id, label: data.week_name ?? 'Semana' })
            }
            if (options.length === 0) return null
            return (
              <label className="mt-4 flex max-w-sm flex-col gap-1 text-sm font-medium text-slate-300">
                Semana
                <SelectControl
                  value={data.week_id ?? ''}
                  onChange={(event) => void changeWeek(event.target.value)}
                  disabled={savingWeek}
                  aria-label="Semana"
                  className={`${controlClass} mt-1 w-full text-sm`}
                  options={[{ value: '', label: 'Sin semana' }, ...options]}
                />
              </label>
            )
          })()}

          <ul className="mt-6 flex flex-col gap-2">
            {data.entries.map((entry) => (
              <li
                key={entry.exercise_id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-700 bg-slate-800/50 px-4 py-3"
              >
                <span className="font-medium text-slate-100">{entry.exercise_name}</span>
                <span className="text-sm text-slate-400">
                  {entry.actual_weight_kg} kg{' '}
                  <span className="text-slate-500">(objetivo {entry.target_weight_kg} kg)</span>
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  )
}

export default StrengthTestLogDetailPage
