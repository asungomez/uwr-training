import { CalendarCheck, ChevronRight } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { useQuery } from '@/api/client'
import { formatLogDate } from '@/components/features/trainings/logFormat'
import Pagination from '@/components/molecules/Pagination'

const PAGE_SIZE = 10

/** The current athlete's own strength-test logs, most recent first (paginated).
 *  Each row links to the full log. */
function StrengthTestLogList() {
  const [page, setPage] = useState(1)
  const { data, isLoading } = useQuery(
    '/strength-test-logs',
    { params: { query: { page, page_size: PAGE_SIZE } } },
    { keepPreviousData: true },
  )

  const logs = data?.items ?? []
  const pageCount = Math.ceil((data?.total_count ?? 0) / PAGE_SIZE)

  return (
    <div className="mt-10 border-t border-slate-800 pt-6">
      <h2 className="text-lg font-semibold text-slate-100">Tus registros</h2>

      {isLoading && <p className="mt-3 text-sm text-slate-400">Cargando…</p>}

      {data && logs.length === 0 && (
        <p className="mt-3 text-sm text-slate-500">Todavía no has hecho ninguna prueba.</p>
      )}

      {logs.length > 0 && (
        <>
          <ul className="mt-3 flex flex-col gap-2">
            {logs.map((log) => (
              <li key={log.id}>
                <Link
                  to={`/pruebas/fuerza/registros/${log.id}`}
                  className="flex items-center justify-between gap-3 rounded-lg border border-slate-700 bg-slate-800/50 px-4 py-3 transition-colors hover:bg-slate-800"
                >
                  <span className="flex min-w-0 items-center gap-3">
                    <CalendarCheck size={16} className="shrink-0 text-emerald-400" />
                    <span className="flex min-w-0 flex-col">
                      <span className="text-slate-200">{formatLogDate(log.performed_at)}</span>
                      <span className="truncate text-sm text-slate-400">
                        Peso corporal: {log.bodyweight_kg} kg
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

export default StrengthTestLogList
