import { CalendarCheck, ChevronRight } from 'lucide-react'
import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { useQuery } from '@/api/client'
import type { components } from '@/api/schema'
import { formatLogDate } from '@/components/features/trainings/logFormat'
import FilterSelect from '@/components/molecules/FilterSelect'
import Pagination from '@/components/molecules/Pagination'

type Category = components['schemas']['TrainingLogCategory']
type TrainingLog = components['schemas']['TrainingLogSummaryResponse']

const PAGE_SIZE = 10

const categoryLabel: Record<Category, string> = {
  gym: 'Gimnasio',
  pool: 'Piscina',
  cardio: 'Cardio',
}

const filterOptions = [
  { value: '', label: 'Todos' },
  { value: 'gym', label: 'Gimnasio' },
  { value: 'pool', label: 'Piscina' },
  { value: 'cardio', label: 'Cardio' },
]

/** Where a log row links: the admin's read-only detail for that log. Cardio and
 *  gym/pool live on different detail pages. */
function logHref(entryId: string, log: TrainingLog): string {
  const kind = log.category === 'cardio' ? 'cardio' : 'sesion'
  return `/usuarios/${entryId}/registros/${kind}/${log.training_id}/${log.id}`
}

/** The "Entrenamientos" tab: the athlete's logged sessions across gym, pool and
 *  cardio, most recent first, with a category filter. Each row links to the log. */
function UserTrainingsTab() {
  const { id } = useParams<{ id: string }>()
  const entryId = id ?? ''
  const [category, setCategory] = useState<Category | ''>('')
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery(
    '/auth/users/{user_id}/training-logs',
    {
      params: {
        path: { user_id: entryId },
        query: { page, page_size: PAGE_SIZE, ...(category ? { category } : {}) },
      },
    },
    { keepPreviousData: true },
  )

  const logs = data?.items ?? []
  const pageCount = Math.ceil((data?.total_count ?? 0) / PAGE_SIZE)

  function changeCategory(value: string) {
    setCategory(value as Category | '')
    setPage(1) // a narrower list may have fewer pages; restart at the first.
  }

  return (
    <div className="mt-6">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-slate-100">Registros</h2>
        <FilterSelect
          value={category}
          onChange={changeCategory}
          options={filterOptions}
          label="Filtrar por categoría"
        />
      </div>

      {isLoading && <p className="mt-3 text-sm text-slate-400">Cargando…</p>}

      {data && logs.length === 0 && (
        <p className="mt-3 text-sm text-slate-500">
          {category
            ? 'No hay registros de esta categoría.'
            : 'Este usuario todavía no ha registrado ningún entrenamiento.'}
        </p>
      )}

      {logs.length > 0 && (
        <>
          <ul className="mt-3 flex flex-col gap-2">
            {logs.map((log) => {
              const subtitle = [log.activity, log.note].filter(Boolean).join(' · ')
              return (
                <li key={log.id}>
                  <Link
                    to={logHref(entryId, log)}
                    className="flex items-center justify-between gap-3 rounded-lg border border-slate-700 bg-slate-800/50 px-4 py-3 transition-colors hover:bg-slate-800"
                  >
                    <span className="flex min-w-0 items-center gap-3">
                      <CalendarCheck size={16} className="shrink-0 text-emerald-400" />
                      <span className="flex min-w-0 flex-col">
                        <span className="text-slate-200">{formatLogDate(log.performed_at)}</span>
                        <span className="truncate text-sm text-slate-400">
                          {[categoryLabel[log.category], log.training_title, subtitle || null]
                            .filter(Boolean)
                            .join(' · ')}
                        </span>
                      </span>
                    </span>
                    <ChevronRight size={16} className="shrink-0 text-slate-500" />
                  </Link>
                </li>
              )
            })}
          </ul>
          <Pagination page={page} pageCount={pageCount} onPageChange={setPage} />
        </>
      )}
    </div>
  )
}

export default UserTrainingsTab
