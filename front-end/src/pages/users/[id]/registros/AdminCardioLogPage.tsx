import { ChevronRight } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'

import { useQuery } from '@/api/client'
import { formatLogDate } from '@/components/features/trainings/logFormat'

/** Admin read-only view of one of an athlete's cardio logs, reached from the user's
 *  "Entrenamientos" tab. */
function AdminCardioLogPage() {
  const { id, trainingId, logId } = useParams<{ id: string; trainingId: string; logId: string }>()
  const entryId = id ?? ''

  const user = useQuery('/auth/users/{entry_id}', {
    params: { path: { entry_id: entryId } },
  })
  const { data, isLoading, error } = useQuery('/cardio-trainings/{training_id}/logs/{log_id}', {
    params: { path: { training_id: trainingId ?? '', log_id: logId ?? '' } },
  })

  return (
    <section>
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
          to={`/usuarios/${entryId}/entrenamientos`}
          className="transition-colors hover:text-slate-200"
        >
          Entrenamientos
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
          {data.exercise && <p className="mt-2 text-slate-200">{data.exercise}</p>}
          {data.note && <p className="mt-2 text-slate-300">{data.note}</p>}
        </div>
      )}
    </section>
  )
}

export default AdminCardioLogPage
