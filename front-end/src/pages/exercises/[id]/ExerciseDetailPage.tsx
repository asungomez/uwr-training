import { ChevronRight, Pencil, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { api, useMutate, useQuery } from '@/api/client'
import { errorMessage } from '@/api/errors'
import { useAuth } from '@/auth/context'
import EditExerciseModal from '@/components/features/exercises/EditExerciseModal'
import { ExerciseTypeBadge } from '@/components/features/exercises/exerciseBadges'
import ConfirmDialog from '@/components/molecules/ConfirmDialog'
import Markdown from '@/components/molecules/Markdown'
import { useToast } from '@/components/toast/context'

function ExerciseDetailPage() {
  const { id } = useParams<{ id: string }>()
  const exerciseId = id ?? ''
  const { data, isLoading, error } = useQuery('/exercises/{exercise_id}', {
    params: { path: { exercise_id: exerciseId } },
  })
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'
  const toast = useToast()
  const mutate = useMutate()
  const navigate = useNavigate()

  const [editing, setEditing] = useState(false)
  const [confirmingDelete, setConfirmingDelete] = useState(false)
  const [deletePending, setDeletePending] = useState(false)
  const [deleteError, setDeleteError] = useState<string | undefined>(undefined)

  async function confirmDelete() {
    setDeletePending(true)
    setDeleteError(undefined)
    const { error: deleteErr } = await api.DELETE('/exercises/{exercise_id}', {
      params: { path: { exercise_id: exerciseId } },
    })
    setDeletePending(false)
    if (deleteErr) {
      setDeleteError(errorMessage(deleteErr))
      return
    }
    toast.success('Ejercicio eliminado.')
    await mutate(['/exercises'])
    void navigate('/ejercicios')
  }

  return (
    <section>
      <nav className="flex items-center gap-1 text-sm text-slate-400" aria-label="Migas de pan">
        <Link to="/ejercicios" className="transition-colors hover:text-slate-200">
          Ejercicios
        </Link>
        <ChevronRight size={14} />
        <span className="text-slate-200">{data?.name ?? '…'}</span>
      </nav>

      {isLoading && <p className="mt-4 text-slate-400">Cargando…</p>}
      {error && <p className="mt-4 text-red-400">No se ha encontrado el ejercicio.</p>}

      {data && (
        <div className="mt-6 max-w-2xl">
          <div className="flex flex-wrap items-center gap-3">
            <h2 className="text-2xl font-semibold tracking-tight text-slate-100">{data.name}</h2>
            <ExerciseTypeBadge type={data.type} />
          </div>

          {data.video_url ? (
            <video
              src={data.video_url}
              poster={data.thumbnail_url ?? undefined}
              controls
              className="mt-4 w-full rounded-lg border border-slate-700"
            />
          ) : (
            data.thumbnail_url && (
              <img
                src={data.thumbnail_url}
                alt=""
                className="mt-4 w-full rounded-lg border border-slate-700 object-contain"
              />
            )
          )}

          {data.description ? (
            <Markdown className="mt-4 text-slate-300">{data.description}</Markdown>
          ) : (
            <p className="mt-4 text-slate-500">Sin descripción.</p>
          )}

          {data.related_exercises.length > 0 && (
            <div className="mt-8">
              <h3 className="text-lg font-semibold text-slate-100">Ejercicios alternativos</h3>
              <ul className="mt-3 flex flex-col gap-3">
                {data.related_exercises.map((related) => (
                  <li
                    key={related.related_exercise_id}
                    className="flex gap-4 rounded-lg border border-slate-700 bg-slate-800/50 p-4"
                  >
                    {related.related_exercise_thumbnail_url && (
                      <Link to={`/ejercicios/${related.related_exercise_id}`} className="shrink-0">
                        <img
                          src={related.related_exercise_thumbnail_url}
                          alt=""
                          loading="lazy"
                          className="h-16 w-24 rounded-md object-cover"
                        />
                      </Link>
                    )}
                    <div className="min-w-0">
                      <Link
                        to={`/ejercicios/${related.related_exercise_id}`}
                        className="font-medium text-indigo-400 transition-colors hover:text-indigo-300"
                      >
                        {related.related_exercise_name}
                      </Link>
                      {related.note && (
                        <p className="mt-1 text-sm text-slate-300">{related.note}</p>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {isAdmin && (
            <div className="mt-6 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => setEditing(true)}
                className="inline-flex items-center gap-2 rounded-md border border-slate-600 px-4 py-2 text-sm font-medium text-slate-200 transition-colors hover:bg-slate-800 focus:ring-2 focus:ring-indigo-400 focus:outline-none"
              >
                <Pencil size={16} />
                Editar
              </button>
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
        <>
          <EditExerciseModal exercise={editing ? data : null} onClose={() => setEditing(false)} />
          <ConfirmDialog
            open={confirmingDelete}
            title="Eliminar ejercicio"
            message={`¿Seguro que quieres eliminar «${data.name}»? Esta acción no se puede deshacer.`}
            confirmLabel={deletePending ? 'Eliminando…' : 'Eliminar'}
            pending={deletePending}
            destructive
            error={deleteError}
            onConfirm={() => void confirmDelete()}
            onCancel={() => setConfirmingDelete(false)}
          />
        </>
      )}
    </section>
  )
}

export default ExerciseDetailPage
