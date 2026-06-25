import { useState } from 'react'

import { useQuery } from '@/api/client'
import { formatLogDate } from '@/components/features/trainings/logFormat'
import Pagination from '@/components/molecules/Pagination'

const PAGE_SIZE = 10

interface ExerciseLogListProps {
  exerciseId: string
}

/** The current athlete's past occurrences of this exercise (most recent first,
 *  paginated): when, in which training, and the parameter values recorded — a
 *  reference for what they used last time. Shown on the exercise detail page and
 *  in the in-training exercise panel. */
function ExerciseLogList({ exerciseId }: ExerciseLogListProps) {
  const [page, setPage] = useState(1)
  const { data, isLoading } = useQuery(
    '/exercises/{exercise_id}/logs',
    { params: { path: { exercise_id: exerciseId }, query: { page, page_size: PAGE_SIZE } } },
    { keepPreviousData: true },
  )

  const entries = data?.items ?? []
  const pageCount = Math.ceil((data?.total_count ?? 0) / PAGE_SIZE)

  return (
    <div>
      <h3 className="text-lg font-semibold text-slate-100">Tu historial</h3>

      {isLoading && <p className="mt-3 text-sm text-slate-400">Cargando…</p>}

      {data && entries.length === 0 && (
        <p className="mt-3 text-sm text-slate-500">Todavía no has hecho este ejercicio.</p>
      )}

      {entries.length > 0 && (
        <>
          <ul className="mt-3 flex flex-col gap-2">
            {entries.map((entry) => (
              <li
                key={entry.log_id}
                className="rounded-lg border border-slate-700 bg-slate-800/50 p-3"
              >
                <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
                  <span className="text-sm text-slate-200">
                    {formatLogDate(entry.performed_at)}
                  </span>
                  {entry.training_title && (
                    <span className="text-xs text-slate-500">{entry.training_title}</span>
                  )}
                </div>
                {entry.as_alternative_for && (
                  <p className="mt-0.5 text-xs text-amber-300">
                    como alternativa de {entry.as_alternative_for}
                  </p>
                )}
                {entry.parameter_values.length > 0 ? (
                  <dl className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-sm">
                    {entry.parameter_values.map((value) => (
                      <div key={value.name} className="flex gap-1.5">
                        <dt className="text-slate-400">{value.name}:</dt>
                        <dd className="text-slate-200">{value.value}</dd>
                      </div>
                    ))}
                  </dl>
                ) : (
                  <p className="mt-1 text-xs text-slate-500">Sin parámetros registrados.</p>
                )}
              </li>
            ))}
          </ul>
          <Pagination page={page} pageCount={pageCount} onPageChange={setPage} />
        </>
      )}
    </div>
  )
}

export default ExerciseLogList
