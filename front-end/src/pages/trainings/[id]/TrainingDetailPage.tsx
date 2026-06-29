import { ChevronRight, Copy, FileText, Pencil, Play, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'

import { api, useMutate, useQuery } from '@/api/client'
import { errorMessage } from '@/api/errors'
import { useAuth } from '@/auth/context'
import ExercisePanel from '@/components/features/trainings/ExercisePanel'
import SessionLogList from '@/components/features/trainings/SessionLogList'
import { CategoryBadge, SubtypeBadge } from '@/components/features/trainings/trainingBadges'
import { openTrainingPdf } from '@/components/features/trainings/trainingPdf'
import TrainingItemView from '@/components/features/trainings/TrainingItemView'
import {
  categoryLabels,
  categorySlugs,
  subtypeLabels,
  subtypeSlugs,
} from '@/components/features/trainings/trainingLabels'
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

  // The athlete's latest strength-test result per exercise, to turn a series' load %
  // into an absolute kg. Keyed by exercise id.
  const { data: latestResults } = useQuery('/strength-test-logs/latest-results', {})
  const testWeightByExercise = new Map(
    (latestResults?.results ?? []).map((result) => [result.exercise_id, result.weight_kg]),
  )

  // ?ejercicio=<id> opens that exercise in the side panel; selecting another just
  // replaces the param (no history entry, so Back leaves the training cleanly).
  const [searchParams, setSearchParams] = useSearchParams()
  const selectedExerciseId = searchParams.get('ejercicio')

  function selectExercise(exerciseId: string) {
    setSearchParams(
      (params) => {
        params.set('ejercicio', exerciseId)
        return params
      },
      { replace: true },
    )
  }

  function closeExercise() {
    setSearchParams(
      (params) => {
        params.delete('ejercicio')
        return params
      },
      { replace: true },
    )
  }

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
      <nav
        className="flex flex-wrap items-center gap-1 text-sm break-words text-slate-400"
        aria-label="Migas de pan"
      >
        <Link to="/entrenamientos" className="transition-colors hover:text-slate-200">
          Entrenamientos
        </Link>
        {data && (
          <>
            <ChevronRight size={14} />
            <Link
              to={`/entrenamientos/${categorySlugs[data.category]}`}
              className="transition-colors hover:text-slate-200"
            >
              {categoryLabels[data.category]}
            </Link>
            <ChevronRight size={14} />
            <Link
              to={`/entrenamientos/${categorySlugs[data.category]}/${subtypeSlugs[data.subtype]}`}
              className="transition-colors hover:text-slate-200"
            >
              {subtypeLabels[data.subtype]}
            </Link>
          </>
        )}
        <ChevronRight size={14} />
        <span className="text-slate-200">{data?.title ?? '…'}</span>
      </nav>

      {/* Two columns on desktop when an exercise is open: training (left) +
          exercise panel (right). The panel is a full-screen overlay on mobile. */}
      <div
        className={
          selectedExerciseId
            ? 'lg:grid lg:grid-cols-[minmax(0,1fr)_minmax(0,28rem)] lg:items-start lg:gap-8'
            : ''
        }
      >
        <div className="min-w-0">
          {isLoading && <p className="mt-4 text-slate-400">Cargando…</p>}
          {error && <p className="mt-4 text-red-400">No se ha encontrado el entrenamiento.</p>}

          {data && (
            <div className="mt-6">
              <h1 className="text-2xl font-semibold tracking-tight break-words text-slate-100">
                {data.title ?? <span className="text-slate-500">{BLANK}</span>}
              </h1>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <CategoryBadge category={data.category} />
                <SubtypeBadge subtype={data.subtype} />
              </div>

              <div className="mt-4 flex flex-wrap gap-2">
                <Link
                  to={`/entrenamientos/${trainingId}/registrar`}
                  className="inline-flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-500 focus:ring-2 focus:ring-indigo-400 focus:outline-none"
                >
                  <Play size={16} />
                  Empezar
                </Link>
                <button
                  type="button"
                  onClick={() => openTrainingPdf(data)}
                  className="inline-flex items-center gap-2 rounded-md border border-slate-600 px-4 py-2 text-sm font-medium text-slate-200 transition-colors hover:bg-slate-800 focus:ring-2 focus:ring-indigo-400 focus:outline-none"
                >
                  <FileText size={16} />
                  PDF
                </button>
              </div>

              {data.blocks.length > 0 && (
                <div className="mt-8 flex flex-col">
                  {data.blocks.map((block, index) => (
                    <div key={block.id}>
                      {index > 0 && <hr className="my-6 border-slate-800" />}
                      <h2 className="text-xl font-semibold text-slate-100">{block.name}</h2>
                      {block.sub_blocks.length > 0 ? (
                        <div className="mt-4 flex flex-col gap-4 border-l-2 border-slate-800 pl-4">
                          {block.sub_blocks.map((sub) => (
                            <div key={sub.id}>
                              <h3 className="font-medium text-slate-200">{sub.name}</h3>
                              {sub.notes && (
                                <p className="mt-1 text-sm text-slate-400">{sub.notes}</p>
                              )}
                              {sub.items.length > 0 && (
                                <ol className="mt-2 flex list-decimal flex-col gap-1 pl-5 text-sm marker:text-slate-500">
                                  {sub.items.map((item) => (
                                    <TrainingItemView
                                      key={item.id}
                                      item={item}
                                      onSelectExercise={selectExercise}
                                      latestTestWeight={
                                        item.exercise_id
                                          ? (testWeightByExercise.get(item.exercise_id) ?? null)
                                          : null
                                      }
                                    />
                                  ))}
                                </ol>
                              )}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="mt-2 text-sm text-slate-500">
                          Aquí irá el bloque de entrenamiento.
                        </p>
                      )}
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
                  <Link
                    to={`/entrenamientos/${categorySlugs[data.category]}/${subtypeSlugs[data.subtype]}/nuevo?copiar_de=${trainingId}`}
                    className="inline-flex items-center gap-2 rounded-md border border-slate-600 px-4 py-2 text-sm font-medium text-slate-200 transition-colors hover:bg-slate-800 focus:ring-2 focus:ring-indigo-400 focus:outline-none"
                  >
                    <Copy size={16} />
                    Copiar entrenamiento
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

              <SessionLogList trainingId={trainingId} />
            </div>
          )}
        </div>

        {selectedExerciseId && (
          <ExercisePanel
            exerciseId={selectedExerciseId}
            onClose={closeExercise}
            onSelectExercise={selectExercise}
          />
        )}
      </div>

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
