import { ChevronRight, Pencil, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { api, useMutate, useQuery } from '@/api/client'
import { errorMessage } from '@/api/errors'
import { useAuth } from '@/auth/context'
import { CategoryBadge, SubtypeBadge } from '@/components/features/trainings/trainingBadges'
import ConfirmDialog from '@/components/molecules/ConfirmDialog'
import { useToast } from '@/components/toast/context'

const BLANK = 'Sin título'

function TrainingDetailPage() {
  const { id } = useParams<{ id: string }>()
  const trainingId = id ?? ''
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'
  const toast = useToast()
  const mutate = useMutate()
  const navigate = useNavigate()

  const { data, isLoading, error } = useQuery('/trainings/{training_id}', {
    params: { path: { training_id: trainingId } },
  })

  const [confirmingDelete, setConfirmingDelete] = useState(false)
  const [deletePending, setDeletePending] = useState(false)
  const [deleteError, setDeleteError] = useState<string | undefined>(undefined)

  async function confirmDelete() {
    setDeletePending(true)
    setDeleteError(undefined)
    const { error: deleteErr } = await api.DELETE('/trainings/{training_id}', {
      params: { path: { training_id: trainingId } },
    })
    setDeletePending(false)
    if (deleteErr) {
      setDeleteError(errorMessage(deleteErr))
      return
    }
    toast.success('Entrenamiento eliminado.')
    await mutate(['/trainings'])
    void navigate('/entrenamientos')
  }

  return (
    <section>
      <nav className="flex items-center gap-1 text-sm text-slate-400" aria-label="Migas de pan">
        <Link to="/entrenamientos" className="transition-colors hover:text-slate-200">
          Entrenamientos
        </Link>
        <ChevronRight size={14} />
        <span className="text-slate-200">{data?.title ?? '…'}</span>
      </nav>

      {isLoading && <p className="mt-4 text-slate-400">Cargando…</p>}
      {error && <p className="mt-4 text-red-400">No se ha encontrado el entrenamiento.</p>}

      {data && (
        <div className="mt-6">
          <h1 className="text-2xl font-semibold tracking-tight text-slate-100">
            {data.title ?? <span className="text-slate-500">{BLANK}</span>}
          </h1>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <CategoryBadge category={data.category} />
            <SubtypeBadge subtype={data.subtype} />
          </div>

          {data.blocks.length > 0 && (
            <div className="mt-8 flex flex-col gap-4">
              {data.blocks.map((block) => (
                <div key={block.id} className="rounded-lg border border-slate-700 bg-slate-800 p-4">
                  <h2 className="text-lg font-semibold text-slate-100">{block.name}</h2>
                  <p className="mt-2 text-sm text-slate-500">
                    Aquí irá el bloque de entrenamiento.
                  </p>
                </div>
              ))}
            </div>
          )}

          {isAdmin && (
            <div className="mt-6 flex flex-wrap gap-2">
              <Link
                to={`/entrenamientos/${trainingId}/editar`}
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
          title="Eliminar entrenamiento"
          message={`¿Seguro que quieres eliminar «${data.title ?? BLANK}»? Esta acción no se puede deshacer.`}
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

export default TrainingDetailPage
