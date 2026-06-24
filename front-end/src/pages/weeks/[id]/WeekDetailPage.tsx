import { ChevronRight, Pencil, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { api, useMutate, useQuery } from '@/api/client'
import { errorMessage } from '@/api/errors'
import { useAuth } from '@/auth/context'
import { categoryLabels, subtypeLabels } from '@/components/features/trainings/trainingLabels'
import { PhaseBadge } from '@/components/features/weeks/PhaseBadge'
import ConfirmDialog from '@/components/molecules/ConfirmDialog'
import { useToast } from '@/components/toast/context'

function WeekDetailPage() {
  const { id } = useParams<{ id: string }>()
  const weekId = id ?? ''
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'
  const toast = useToast()
  const mutate = useMutate()
  const navigate = useNavigate()

  const { data, isLoading, error } = useQuery('/weeks/{week_id}', {
    params: { path: { week_id: weekId } },
  })

  const [confirmingDelete, setConfirmingDelete] = useState(false)
  const [deletePending, setDeletePending] = useState(false)
  const [deleteError, setDeleteError] = useState<string | undefined>(undefined)

  async function confirmDelete() {
    setDeletePending(true)
    setDeleteError(undefined)
    const { error: deleteErr } = await api.DELETE('/weeks/{week_id}', {
      params: { path: { week_id: weekId } },
    })
    setDeletePending(false)
    if (deleteErr) {
      setDeleteError(errorMessage(deleteErr))
      return
    }
    toast.success('Semana eliminada.')
    await mutate(['/weeks'])
    void navigate('/calendario')
  }

  return (
    <section>
      <nav className="flex items-center gap-1 text-sm text-slate-400" aria-label="Migas de pan">
        <Link to="/calendario" className="transition-colors hover:text-slate-200">
          Calendario
        </Link>
        <ChevronRight size={14} />
        <span className="text-slate-200">{data?.name ?? '…'}</span>
      </nav>

      {isLoading && <p className="mt-4 text-slate-400">Cargando…</p>}
      {error && <p className="mt-4 text-red-400">No se ha encontrado la semana.</p>}

      {data && (
        <div className="mt-6 max-w-2xl">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-semibold tracking-tight text-slate-100">{data.name}</h1>
            <PhaseBadge phase={data.phase} />
          </div>
          {data.recommended_date && <p className="mt-1 text-slate-400">{data.recommended_date}</p>}

          <h2 className="mt-8 text-lg font-semibold text-slate-100">Sesiones recomendadas</h2>
          {data.requirements.length > 0 ? (
            <ul className="mt-3 flex flex-col gap-2">
              {data.requirements.map((req) => (
                <li
                  key={req.id}
                  className="flex items-center justify-between gap-3 rounded-lg border border-slate-700 bg-slate-800/50 px-4 py-3"
                >
                  <span className="text-slate-200">
                    {categoryLabels[req.category]} · {subtypeLabels[req.subtype]}
                  </span>
                  <span className="font-medium text-slate-100">
                    {req.count} {req.count === 1 ? 'sesión' : 'sesiones'}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-3 text-sm text-slate-500">
              Esta semana no tiene sesiones recomendadas.
            </p>
          )}

          {isAdmin && (
            <div className="mt-6 flex flex-wrap gap-2">
              <Link
                to={`/calendario/${weekId}/editar`}
                className="inline-flex items-center gap-2 rounded-md border border-slate-600 px-4 py-2 text-sm font-medium text-slate-200 transition-colors hover:bg-slate-800 focus:ring-2 focus:ring-indigo-400 focus:outline-none"
              >
                <Pencil size={16} />
                Editar
              </Link>
              <button
                type="button"
                onClick={() => {
                  setDeleteError(undefined)
                  setConfirmingDelete(true)
                }}
                className="inline-flex items-center gap-2 rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-red-500 focus:ring-2 focus:ring-red-400 focus:outline-none"
              >
                <Trash2 size={16} />
                Eliminar
              </button>
            </div>
          )}
        </div>
      )}

      {isAdmin && data && (
        <ConfirmDialog
          open={confirmingDelete}
          title="Eliminar semana"
          message={`¿Seguro que quieres eliminar «${data.name}»? Esta acción no se puede deshacer.`}
          confirmLabel={deletePending ? 'Eliminando…' : 'Eliminar'}
          pending={deletePending}
          destructive
          error={deleteError}
          onConfirm={() => void confirmDelete()}
          onCancel={() => setConfirmingDelete(false)}
        />
      )}
    </section>
  )
}

export default WeekDetailPage
