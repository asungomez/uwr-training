import { Check, ChevronRight, X } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'

import { useQuery } from '@/api/client'
import { formatLogDate } from '@/components/features/trainings/logFormat'

function SessionLogDetailPage() {
  const { id, logId } = useParams<{ id: string; logId: string }>()
  const trainingId = id ?? ''

  const training = useQuery('/trainings/{training_id}', {
    params: { path: { training_id: trainingId } },
  })
  const { data, isLoading, error } = useQuery('/trainings/{training_id}/logs/{log_id}', {
    params: { path: { training_id: trainingId, log_id: logId ?? '' } },
  })

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
