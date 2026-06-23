import { Pencil, Plus, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { api, useMutate, useQuery } from '@/api/client'
import { errorMessage } from '@/api/errors'
import type { components } from '@/api/schema'
import ConfirmDialog from '@/components/molecules/ConfirmDialog'
import FilterSelect from '@/components/molecules/FilterSelect'
import Pagination from '@/components/molecules/Pagination'
import SearchInput from '@/components/molecules/SearchInput'
import { useAuth } from '@/auth/context'
import { useToast } from '@/components/toast/context'
import { useDebouncedValue } from '@/hooks/useDebouncedValue'
import { useUrlListState } from '@/hooks/useUrlListState'
import EditExerciseModal from '@/components/features/exercises/EditExerciseModal'
import { ExerciseTypeBadge } from '@/components/features/exercises/exerciseBadges'
import Markdown from '@/components/molecules/Markdown'
import NewExerciseModal from '@/components/features/exercises/NewExerciseModal'

const PAGE_SIZE = 12

type Exercise = components['schemas']['ExerciseResponse']
type ExerciseType = Exercise['type']

const TYPES = ['gym', 'pool'] as const

const cardTint: Record<ExerciseType, string> = {
  gym: 'border-amber-500/30 bg-amber-500/10 hover:border-amber-500/50',
  pool: 'border-sky-500/30 bg-sky-500/10 hover:border-sky-500/50',
}

interface ExerciseCardProps {
  exercise: Exercise
  isAdmin: boolean
  onOpen: (exercise: Exercise) => void
  onEdit: (exercise: Exercise) => void
  onDelete: (exercise: Exercise) => void
}

function ExerciseCard({ exercise, isAdmin, onOpen, onEdit, onDelete }: ExerciseCardProps) {
  return (
    <article
      onClick={() => onOpen(exercise)}
      className={`flex cursor-pointer flex-col gap-2 rounded-lg border p-4 transition-colors ${cardTint[exercise.type]}`}
    >
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-medium text-slate-100">{exercise.name}</h3>
        <ExerciseTypeBadge type={exercise.type} />
      </div>
      {exercise.description && (
        <Markdown className="line-clamp-3 text-sm text-slate-300">{exercise.description}</Markdown>
      )}
      {isAdmin && (
        <div className="mt-auto flex justify-end gap-1 pt-2">
          <button
            type="button"
            onClick={(event) => {
              event.stopPropagation()
              onEdit(exercise)
            }}
            aria-label={`Editar ${exercise.name}`}
            className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-slate-300 transition-colors hover:bg-slate-700/60 hover:text-white focus:ring-2 focus:ring-indigo-400 focus:outline-none"
          >
            <Pencil size={14} />
            Editar
          </button>
          <button
            type="button"
            onClick={(event) => {
              event.stopPropagation()
              onDelete(exercise)
            }}
            aria-label={`Eliminar ${exercise.name}`}
            className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-red-300 transition-colors hover:bg-red-500/15 hover:text-red-200 focus:ring-2 focus:ring-red-400 focus:outline-none"
          >
            <Trash2 size={14} />
            Eliminar
          </button>
        </div>
      )}
    </article>
  )
}

function ExercisesPage() {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'
  const toast = useToast()
  const mutate = useMutate()
  const navigate = useNavigate()
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Exercise | null>(null)
  const [deleting, setDeleting] = useState<Exercise | null>(null)
  const [deletePending, setDeletePending] = useState(false)
  const [deleteError, setDeleteError] = useState<string | undefined>(undefined)

  const { page, search, setPage, setSearch, getFilter, setFilter } = useUrlListState()
  const type = getFilter('type', TYPES) as ExerciseType | ''
  const debouncedSearch = useDebouncedValue(search.trim(), 300)

  function requestDelete(exercise: Exercise) {
    setDeleteError(undefined)
    setDeleting(exercise)
  }

  async function confirmDelete() {
    if (!deleting) return
    setDeletePending(true)
    setDeleteError(undefined)
    const { error } = await api.DELETE('/exercises/{exercise_id}', {
      params: { path: { exercise_id: deleting.id } },
    })
    setDeletePending(false)
    if (error) {
      setDeleteError(errorMessage(error))
      return
    }
    toast.success('Ejercicio eliminado.')
    await mutate(['/exercises'])
    setDeleting(null)
  }

  const { data, isLoading, error } = useQuery(
    '/exercises',
    {
      params: {
        query: {
          page,
          page_size: PAGE_SIZE,
          ...(debouncedSearch ? { search: debouncedSearch } : {}),
          ...(type ? { type } : {}),
        },
      },
    },
    { keepPreviousData: true },
  )
  const exercises = data?.items
  const pageCount = Math.ceil((data?.total_count ?? 0) / PAGE_SIZE)

  return (
    <section>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-2xl font-semibold tracking-tight">Ejercicios</h2>
        {isAdmin && (
          <button
            type="button"
            onClick={() => setModalOpen(true)}
            className="inline-flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-500 focus:ring-2 focus:ring-indigo-400 focus:outline-none"
          >
            <Plus size={16} />
            Nuevo ejercicio
          </button>
        )}
      </div>

      {isAdmin && (
        <>
          <NewExerciseModal open={modalOpen} onClose={() => setModalOpen(false)} />
          <EditExerciseModal exercise={editing} onClose={() => setEditing(null)} />
          <ConfirmDialog
            open={deleting !== null}
            title="Eliminar ejercicio"
            message={`¿Seguro que quieres eliminar «${deleting?.name ?? ''}»? Esta acción no se puede deshacer.`}
            confirmLabel={deletePending ? 'Eliminando…' : 'Eliminar'}
            pending={deletePending}
            destructive
            error={deleteError}
            onConfirm={() => void confirmDelete()}
            onCancel={() => setDeleting(null)}
          />
        </>
      )}

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <SearchInput value={search} onChange={setSearch} placeholder="Buscar por nombre…" />
        <FilterSelect
          value={type}
          onChange={(value) => setFilter('type', value)}
          label="Filtrar por tipo"
          options={[
            { value: '', label: 'Todos los tipos' },
            { value: 'gym', label: 'Gimnasio' },
            { value: 'pool', label: 'Piscina' },
          ]}
        />
      </div>

      {isLoading && <p className="mt-4 text-slate-400">Cargando…</p>}
      {error && <p className="mt-4 text-red-400">No se pudieron cargar los ejercicios.</p>}

      {exercises?.length === 0 && (
        <p className="mt-4 text-slate-400">
          {debouncedSearch || type
            ? 'No hay ejercicios que coincidan con la búsqueda.'
            : 'No hay ningún ejercicio todavía.'}
        </p>
      )}

      {exercises && exercises.length > 0 && (
        <>
          <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {exercises.map((exercise) => (
              <ExerciseCard
                key={exercise.id}
                exercise={exercise}
                isAdmin={isAdmin}
                onOpen={(ex) => void navigate(`/ejercicios/${ex.id}`)}
                onEdit={setEditing}
                onDelete={requestDelete}
              />
            ))}
          </div>
          <Pagination page={page} pageCount={pageCount} onPageChange={setPage} />
        </>
      )}
    </section>
  )
}

export default ExercisesPage
