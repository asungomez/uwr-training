import { CalendarCheck, ChevronRight } from 'lucide-react'
import { Link } from 'react-router-dom'

import { useQuery } from '@/api/client'
import { formatLogDate } from '@/components/features/trainings/logFormat'

interface SessionLogListProps {
  trainingId: string
}

/** The current athlete's own logs for a session, shown at the bottom of its detail
 *  page. Each row links to the full log. */
function SessionLogList({ trainingId }: SessionLogListProps) {
  const { data, isLoading } = useQuery('/trainings/{training_id}/logs', {
    params: { path: { training_id: trainingId } },
  })

  return (
    <div className="mt-10 border-t border-slate-800 pt-6">
      <h2 className="text-lg font-semibold text-slate-100">Tus registros</h2>

      {isLoading && <p className="mt-3 text-sm text-slate-400">Cargando…</p>}

      {data?.length === 0 && (
        <p className="mt-3 text-sm text-slate-500">Todavía no has registrado esta sesión.</p>
      )}

      {data && data.length > 0 && (
        <ul className="mt-3 flex flex-col gap-2">
          {data.map((log) => (
            <li key={log.id}>
              <Link
                to={`/entrenamientos/${trainingId}/registros/${log.id}`}
                className="flex items-center justify-between gap-3 rounded-lg border border-slate-700 bg-slate-800/50 px-4 py-3 transition-colors hover:bg-slate-800"
              >
                <span className="flex min-w-0 items-center gap-3">
                  <CalendarCheck size={16} className="shrink-0 text-emerald-400" />
                  <span className="flex min-w-0 flex-col">
                    <span className="text-slate-200">{formatLogDate(log.performed_at)}</span>
                    {log.note && (
                      <span className="truncate text-sm text-slate-400">{log.note}</span>
                    )}
                  </span>
                </span>
                <ChevronRight size={16} className="shrink-0 text-slate-500" />
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default SessionLogList
