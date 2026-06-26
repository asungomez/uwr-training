import { Check, ChevronRight, X } from 'lucide-react'
import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { api, useMutate, useQuery } from '@/api/client'
import { errorMessage } from '@/api/errors'
import { controlClass } from '@/components/atoms/form/fieldStyles'
import SelectControl from '@/components/atoms/form/SelectControl'
import { formatLogDate } from '@/components/features/trainings/logFormat'
import { useToast } from '@/components/toast/context'

function SessionLogDetailPage() {
  const { id, logId } = useParams<{ id: string; logId: string }>()
  const trainingId = id ?? ''
  const toast = useToast()
  const mutate = useMutate()
  const [savingWeek, setSavingWeek] = useState(false)

  const training = useQuery('/trainings/{training_id}', {
    params: { path: { training_id: trainingId } },
  })
  const { data, isLoading, error } = useQuery('/trainings/{training_id}/logs/{log_id}', {
    params: { path: { training_id: trainingId, log_id: logId ?? '' } },
  })
  // The weeks this session can be assigned to (those recommending its type).
  const form = useQuery('/trainings/{training_id}/log-form', {
    params: { path: { training_id: trainingId } },
  })

  async function changeWeek(weekId: string) {
    setSavingWeek(true)
    const { error: patchError } = await api.PATCH('/trainings/{training_id}/logs/{log_id}/week', {
      params: { path: { training_id: trainingId, log_id: logId ?? '' } },
      body: { week_id: weekId || null },
    })
    setSavingWeek(false)
    if (patchError) {
      toast.error(errorMessage(patchError))
      return
    }
    await mutate([
      '/trainings/{training_id}/logs/{log_id}',
      { params: { path: { training_id: trainingId, log_id: logId ?? '' } } },
    ])
    toast.success('Semana actualizada.')
  }

  return (
    <section>
      <nav className="flex items-center gap-1 text-sm text-slate-400" aria-label="Migas de pan">
        <Link to="/entrenamientos" className="transition-colors hover:text-slate-200">
          Entrenamientos
        </Link>
        <ChevronRight size={14} />
        <Link
          to={`/entrenamientos/${trainingId}`}
          className="transition-colors hover:text-slate-200"
        >
          {training.data?.title ?? '…'}
        </Link>
        <ChevronRight size={14} />
        <span className="text-slate-200">Registro</span>
      </nav>

      {isLoading && <p className="mt-4 text-slate-400">Cargando…</p>}
      {error && <p className="mt-4 text-red-400">No se ha encontrado el registro.</p>}

      {data && (
        <div className="mt-6 max-w-2xl">
          <h1 className="text-2xl font-semibold tracking-tight text-slate-100">
            {formatLogDate(data.performed_at)}
          </h1>
          {data.note && <p className="mt-2 text-slate-300">{data.note}</p>}

          {(() => {
            // Selectable weeks = those still open for this type, plus the log's
            // current week (which may now be full but must stay selectable here).
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

          <ul className="mt-6 flex flex-col gap-3">
            {data.entries.map((entry) => {
              const done = entry.action === 'done'
              return (
                <li
                  key={entry.id}
                  className={`rounded-lg border bg-slate-800/50 p-4 ${
                    done ? 'border-emerald-600/50' : 'border-slate-700 opacity-70'
                  }`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="min-w-0">
                      <span className="font-medium text-slate-100">
                        {done ? entry.performed_exercise_name : entry.planned_exercise_name}
                      </span>
                      {done && entry.is_alternative && (
                        <span className="ml-2 text-xs text-amber-300">
                          (alternativa de {entry.planned_exercise_name})
                        </span>
                      )}
                    </div>
                    <span
                      className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium ${
                        done
                          ? 'bg-emerald-500/20 text-emerald-200'
                          : 'bg-slate-600/40 text-slate-300'
                      }`}
                    >
                      {done ? <Check size={12} /> : <X size={12} />}
                      {done ? 'Hecho' : 'No hecho'}
                    </span>
                  </div>

                  {done && entry.parameter_values.length > 0 && (
                    <dl className="mt-3 flex flex-wrap gap-x-6 gap-y-1 text-sm">
                      {entry.parameter_values.map((value) => (
                        <div key={value.id} className="flex gap-1.5">
                          <dt className="text-slate-400">{value.name}:</dt>
                          <dd className="text-slate-200">{value.value}</dd>
                        </div>
                      ))}
                    </dl>
                  )}
                </li>
              )
            })}
          </ul>
        </div>
      )}
    </section>
  )
}

export default SessionLogDetailPage
