import { ChevronRight } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'

import { useQuery } from '@/api/client'
import { formatLogDate } from '@/components/features/trainings/logFormat'

/** Admin read-only view of one of an athlete's speed-test logs, reached from the
 *  user's "Pruebas" tab. */
function AdminSpeedTestLogPage() {
  const { id, logId } = useParams<{ id: string; logId: string }>()
  const entryId = id ?? ''

  const user = useQuery('/auth/users/{entry_id}', {
    params: { path: { entry_id: entryId } },
  })
  const { data, isLoading, error } = useQuery('/speed-test-logs/{log_id}', {
    params: { path: { log_id: logId ?? '' } },
  })

  return (
    <section className="max-w-2xl">
      <nav
        className="flex flex-wrap items-center gap-1 text-sm break-words text-slate-400"
        aria-label="Migas de pan"
      >
        <Link to="/usuarios" className="transition-colors hover:text-slate-200">
          Usuarios
        </Link>
        <ChevronRight size={14} />
        <Link to={`/usuarios/${entryId}`} className="transition-colors hover:text-slate-200">
          {user.data?.email ?? '…'}
        </Link>
        <ChevronRight size={14} />
        <Link
          to={`/usuarios/${entryId}/pruebas`}
          className="transition-colors hover:text-slate-200"
        >
          Pruebas
        </Link>
        <ChevronRight size={14} />
        <span className="text-slate-200">Prueba de velocidad</span>
      </nav>

      {isLoading && <p className="mt-4 text-slate-400">Cargando…</p>}
      {error && <p className="mt-4 text-red-400">No se ha encontrado el registro.</p>}

      {data && (
        <div className="mt-6">
          <h1 className="text-2xl font-semibold tracking-tight text-slate-100">
            {formatLogDate(data.performed_at)}
          </h1>
          <p className="mt-1 text-slate-200">
            Tiempo: <span className="font-medium">{data.seconds} s</span>
          </p>
        </div>
      )}
    </section>
  )
}

export default AdminSpeedTestLogPage
