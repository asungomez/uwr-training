import { CalendarCheck, ChevronRight } from 'lucide-react'
import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { useQuery } from '@/api/client'
import type { components } from '@/api/schema'
import { formatLogDate } from '@/components/features/trainings/logFormat'
import FilterSelect from '@/components/molecules/FilterSelect'
import Pagination from '@/components/molecules/Pagination'

type TestType = components['schemas']['TestLogType']
type TestLog = components['schemas']['TestLogSummaryResponse']

const PAGE_SIZE = 10

const typeLabel: Record<TestType, string> = {
  strength: 'Fuerza',
  speed: 'Velocidad',
}

const filterOptions = [
  { value: '', label: 'Todas' },
  { value: 'strength', label: 'Fuerza' },
  { value: 'speed', label: 'Velocidad' },
]

/** Where a test-log row links: the admin's read-only detail for that test. */
function logHref(entryId: string, log: TestLog): string {
  const kind = log.type === 'strength' ? 'fuerza' : 'velocidad'
  return `/usuarios/${entryId}/pruebas/${kind}/${log.id}`
}

/** The "Pruebas" tab: the athlete's strength and speed tests, most recent first,
 *  with a type filter. Each row links to the test's read-only detail. */
function UserTestsTab() {
  const { id } = useParams<{ id: string }>()
  const entryId = id ?? ''
  const [type, setType] = useState<TestType | ''>('')
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery(
    '/auth/users/{user_id}/test-logs',
    {
      params: {
        path: { user_id: entryId },
        query: { page, page_size: PAGE_SIZE, ...(type ? { type } : {}) },
      },
    },
    { keepPreviousData: true },
  )

  const logs = data?.items ?? []
  const pageCount = Math.ceil((data?.total_count ?? 0) / PAGE_SIZE)

  function changeType(value: string) {
    setType(value as TestType | '')
    setPage(1) // a narrower list may have fewer pages; restart at the first.
  }

  return (
    <div className="mt-6">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-slate-100">Registros</h2>
        <FilterSelect
          value={type}
          onChange={changeType}
          options={filterOptions}
          label="Filtrar por tipo"
        />
      </div>

      {isLoading && <p className="mt-3 text-sm text-slate-400">Cargando…</p>}

      {data && logs.length === 0 && (
        <p className="mt-3 text-sm text-slate-500">
          {type
            ? 'No hay pruebas de este tipo.'
            : 'Este usuario todavía no ha registrado ninguna prueba.'}
        </p>
      )}

      {logs.length > 0 && (
        <>
          <ul className="mt-3 flex flex-col gap-2">
            {logs.map((log) => (
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
                        {[typeLabel[log.type], log.summary].filter(Boolean).join(' · ')}
                      </span>
                    </span>
                  </span>
                  <ChevronRight size={16} className="shrink-0 text-slate-500" />
                </Link>
              </li>
            ))}
          </ul>
          <Pagination page={page} pageCount={pageCount} onPageChange={setPage} />
        </>
      )}
    </div>
  )
}

export default UserTestsTab
